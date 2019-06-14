function p_kilosort(kilosort_path, temp_path, raw_fname, geom_fname, firings_out_fname, arg_fname)
% cmdstr2 = sprintf("p_ironclust('$(tempdir)','$timeseries$','$geom$','$firings_out$','$(argfile)');");

if exist(temp_path, 'dir') ~= 7
    mkdir(temp_path);
end

% prepare for kilosort execution
addpath(genpath(kilosort_path));
ops = import_ksort_(raw_fname, geom_fname, arg_fname, temp_path);

% Run kilosort
t1=tic;
fprintf('Running kilosort on %s\n', raw_fname);
[rez, DATA, uproj] = preprocessData(ops); % preprocess data and extract spikes for initialization
rez                = fitTemplates(rez, DATA, uproj);  % fit templates iteratively
rez                = fullMPMU(rez, DATA);% extract final spike times (overlapping extraction)
try
    rez = merge_posthoc2(rez);
catch
    fprintf(2, 'merge_posthoc2 error. Reporting pre-merge result\n'); 
end
fprintf('\n\ttook %0.1fs\n', toc(t1));

% Export kilosort
mr_out = export_ksort_(rez, firings_out_fname);

fprintf('Clustering result wrote to %s\n', firings_out_fname);

end %func


%--------------------------------------------------------------------------
function mr_out = export_ksort_(rez, firings_out_fname)

mr_out = zeros(size(rez.st3,1), 3, 'double'); 
mr_out(:,2) = rez.st3(:,1); %time
mr_out(:,3) = rez.st3(:,2); %cluster
writemda(mr_out', firings_out_fname, 'int32');
end %func

%--------------------------------------------------------------------------
function ops = import_ksort_(raw_fname, geom_fname, arg_fname, fpath)
% fpath: output path
S_txt = meta2struct_(arg_fname);
useGPU = 1;
[freq_min, pc_per_chan, sRateHz, spkTh, adjacency_radius, Th1, Th2, nfilt_factor, NT_fac] = struct_get_(S_txt, 'freq_min', 'pc_per_chan', 'samplerate', 'detect_threshold', 'adjacency_radius', 'Th1', 'Th2', 'nfilt_factor', 'NT_fac');
 
spkTh = -abs(spkTh);

% convert to binary file (int16)
fbinary = strrep(raw_fname, '.mda', '.bin');
[Nchannels, ~] = mda2bin_(raw_fname, fbinary, S_txt.detect_sign);

% create a probe file
mrXY_site = csvread(geom_fname);
vcFile_chanMap = fullfile(fpath, 'chanMap.mat');
createChannelMapFile_(vcFile_chanMap, Nchannels, S_txt.samplerate, mrXY_site(:,1), mrXY_site(:,2));
nChans = size(mrXY_site,1);

S_ops = makeStruct_(fpath, fbinary, nChans, vcFile_chanMap, spkTh, useGPU, sRateHz, pc_per_chan, freq_min, adjacency_radius, Th1, Th2, nfilt_factor, NT_fac);
ops = config_kilosort_(S_ops); %obtain ops

end %func

%--------------------------------------------------------------------------
function varargout = struct_get_(varargin)
% Obtain a member of struct
% cvr = cell(size(varargin));
% if varargin is given as cell output is also cell
S = varargin{1};
for iArg=1:nargout
    vcName = varargin{iArg+1};
    if iscell(vcName)
        csName_ = vcName;
        cell_ = cell(size(csName_));
        for iCell = 1:numel(csName_)
            vcName_ = csName_{iCell};
            if isfield(S, vcName_)
                cell_{iCell} = S.(vcName_);
            end
        end %for
        varargout{iArg} = cell_;
    elseif ischar(vcName)
        if isfield(S, vcName)
            varargout{iArg} = S.(vcName);
        else
            varargout{iArg} = [];
        end
    else
        varargout{iArg} = [];
    end
end %for
end %func



%--------------------------------------------------------------------------
function S = makeStruct_(varargin)
%MAKESTRUCT all the inputs must be a variable. 
%don't pass function of variables. ie: abs(X)
%instead create a var AbsX an dpass that name
S = struct();
for i=1:nargin, S.(inputname(i)) =  varargin{i}; end
end %func


%--------------------------------------------------------------------------
function S_chanMap = createChannelMapFile_(vcFile_channelMap, Nchannels, fs, xcoords, ycoords, kcoords)
if nargin<6, kcoords = []; end

connected = true(Nchannels, 1);
chanMap   = 1:Nchannels;
chanMap0ind = chanMap - 1;

xcoords   = xcoords(:);
ycoords   = ycoords(:);

if isempty(kcoords)
    kcoords   = ones(Nchannels,1); % grouping of channels (i.e. tetrode groups)
end

S_chanMap = makeStruct_(chanMap, connected, xcoords, ycoords, kcoords, chanMap0ind, fs);
save(vcFile_channelMap, '-struct', 'S_chanMap')
end %func

%--------------------------------------------------------------------------
% convert mda to int16 binary format, flip polarity if detect sign is
% positive
function [nChans, nSamples] = mda2bin_(raw_fname, fbinary, detect_sign)
dims = readmdadims(raw_fname);
nChans = dims(1);
nSamples = dims(2);

if ~isfile(fbinary)
fid = fopen(fbinary, 'w');
blk_size = 20000 * 60 * 5; % 5 mins for a 20 kHz recording
n_blks = ceil(nSamples/blk_size);
total_size = 0;
disp('Writing .dat from .mda in blocks...')
for i = 1:n_blks
    i_start = ((i-1)*blk_size) + 1;
    if i < n_blks
        i_end = i_start+blk_size-1;
        blk_size_read = blk_size;
    else
        i_end = nSamples;
        blk_size_read = nSamples - i_start + 1;
    end
    fprintf('Block %d of %d - samples %d to %d \n', i, n_blks, i_start, i_end);
    
    mr_block = readmda_block(raw_fname,[1,i_start],[nChans,blk_size_read]);
    % adjust scale to fit int16 range with a margin
    %if isa(mr_block,'single') || isa(mr_block,'double')
    %    uV_per_bit = 2^14 / max(abs(mr_block(:)));
    %    mr_block = int16(mr_block * uV_per_bit);
    %end
    if detect_sign > 0, mr = -mr; end % force negative detection
    fwrite(fid, mr_block, 'int16');
    total_size = total_size + size(mr_block,2);
end
fclose(fid);
fprintf('Total Samples Written: %d\n', total_size);
fprintf('Total Samples in Header: %d\n', nSamples);
end
end %func


%--------------------------------------------------------------------------
% convert mda to int16 binary format, flip polarity if detect sign is
% positive
function [nChans, nSamples] = mda2bin_old(raw_fname, fbinary, detect_sign)

mr = readmda(raw_fname);
% adjust scale to fit int16 range with a margin
if isa(mr,'single') || isa(mr,'double')
    uV_per_bit = 2^14 / max(abs(mr(:)));
    mr = int16(mr * uV_per_bit);
end
[nChans, nSamples] = size(mr);
if detect_sign > 0, mr = -mr; end % force negative detection
fid = fopen(fbinary, 'w');
fwrite(fid, mr, 'int16');
fclose(fid);
end %func

function ops = config_kilosort_(S_opt)

ops = struct();
ops.GPU                 = 1; % whether to run this code on an Nvidia GPU (much faster, mexGPUall first)		
ops.parfor              = 0; % whether to use parfor to accelerate some parts of the algorithm		
ops.verbose             = 1; % whether to print command line progress		
ops.showfigures         = 1; % whether to plot figures during optimization		
		
ops.datatype            = 'bin';  % binary ('dat', 'bin') or 'openEphys'		
ops.fproc               = fullfile(S_opt.fpath, 'temp_wh.dat'); % residual from RAM of preprocessed data		

% the binary file is in this folder
ops.fbinary = S_opt.fbinary;

ops.chanMap = S_opt.vcFile_chanMap;

S_prb = load(ops.chanMap);
nChans = numel(S_prb.chanMap);

ops.Nfilt               = nChans*8;  % number of clusters to use (2-4 times more than Nchan, should be a multiple of 32)     		
ops.nNeighPC            = min(12,nChans); % visualization only (Phy): number of channnels to mask the PCs, leave empty to skip (12)		
ops.nNeigh              = 16; % visualization only (Phy): number of neighboring templates to retain projections of (16)		
		
% options for channel whitening		
ops.whitening           = 'full'; % type of whitening (default 'full', for 'noSpikes' set options for spike detection below)		
ops.nSkipCov            = 1; % compute whitening matrix from every N-th batch (1)		
ops.whiteningRange      = 32; % how many channels to whiten together (Inf for whole probe whitening, should be fine if Nchan<=32)		
		
ops.criterionNoiseChannels = 0.2; % fraction of "noise" templates allowed to span all channel groups (see createChannelMapFile for more info). 		
% other options for controlling the model and optimization		
ops.Nrank               = 3;    % matrix rank of spike template model (3)		
ops.nfullpasses         = 6;    % number of complete passes through data during optimization (6)		
ops.maxFR               = 20000;  % maximum number of spikes to extract per batch (20000)		
ops.fshigh              = S_opt.freq_min;   % frequency for high pass filtering		
ops.ntbuff              = 64;    % samples of symmetrical buffer for whitening and spike detection		
ops.scaleproc           = 200;   % int16 scaling of whitened data		
ops.NT                  = 128*1024+ ops.ntbuff;% this is the batch size (try decreasing if out of memory) 		
% for GPU should be multiple of 32 + ntbuff		
		
% the following options can improve/deteriorate results. 		
% when multiple values are provided for an option, the first two are beginning and ending anneal values, 		
% threshold on projections (like in Kilosort1, can be different for last pass like [10 4])
ops.Th = [S_opt.Th1 S_opt.Th2 S_opt.Th2];  
ops.nannealpasses    = 4;            % should be less than nfullpasses (4)		
ops.shuffle_clusters = 1;            % allow merges and splits during optimization (1)		
ops.mergeT           = .2;           % upper threshold for merging (.1)		
ops.splitT           = .1;           % lower threshold for splitting (.1)		
% how important is the amplitude penalty (like in Kilosort1, 0 means not used, 10 is average, 50 is a lot) 
ops.lam              = [10 20 20];   % large means amplitudes are forced around the mean ([10 30 30])		
% number of samples to average over (annealed from first to second value) 
ops.momentum = 1./[20 400]; 
	
% options for initializing spikes from data		
ops.initialize      = 'fromData';    %'fromData' or 'no'		
ops.spkTh           = S_opt.spkTh;      % spike threshold in standard deviations (4)		
ops.loc_range       = [3  1];  % ranges to detect peaks; plus/minus in time and channel ([3 1])		
ops.long_range      = [30  6]; % ranges to detect isolated peaks ([30 6])		
ops.maskMaxChannels = 5;       % how many channels to mask up/down ([5])		
ops.crit            = .65;     % upper criterion for discarding spike repeates (0.65)		
ops.nFiltMax        = 10000;   % maximum "unique" spikes to consider (10000)		
		
% load predefined principal components (visualization only (Phy): used for features)		
dd                  = load('PCspikes2.mat'); % you might want to recompute this from your own data		
ops.wPCA            = dd.Wi(:,1:7);   % PCs 		
		
% options for posthoc merges (under construction)		
ops.fracse  = 0.1; % binning step along discriminant axis for posthoc merges (in units of sd)		
ops.epu     = Inf;		
		
ops.ForceMaxRAMforDat   = 20e9; % maximum RAM the algorithm will try to use; on Windows it will autodetect.

end % func


%--------------------------------------------------------------------------
% 8/2/17 JJJ: Documentation and test
function S = meta2struct_(vcFile)
    % Convert text file to struct
    S = struct();
    if ~exist_file_(vcFile, 1), return; end
    
    fid = fopen(vcFile, 'r');
    mcFileMeta = textscan(fid, '%s%s', 'Delimiter', '=',  'ReturnOnError', false);
    fclose(fid);
    csName = mcFileMeta{1};
    csValue = mcFileMeta{2};
    for i=1:numel(csName)
        vcName1 = csName{i};
        if vcName1(1) == '~', vcName1(1) = []; end
        try         
            eval(sprintf('%s = ''%s'';', vcName1, csValue{i}));
            eval(sprintf('num = str2double(%s);', vcName1));
            if ~isnan(num)
                eval(sprintf('%s = num;', vcName1));
            end
            eval(sprintf('S = setfield(S, ''%s'', %s);', vcName1, vcName1));
        catch
            fprintf('%s = %s error\n', csName{i}, csValue{i});
        end
    end
    end %func
    
    
    %--------------------------------------------------------------------------
    % 7/21/2018 JJJ: rejecting directories, strictly search for flies
    % 9/26/17 JJJ: Created and tested
    function flag = exist_file_(vcFile, fVerbose)
    if nargin<2, fVerbose = 0; end
    if isempty(vcFile)
        flag = false; 
    elseif iscell(vcFile)
        flag = cellfun(@(x)exist_file_(x, fVerbose), vcFile);
        return;
    else
        S_dir = dir(vcFile);
        if numel(S_dir) == 1
            flag = ~S_dir.isdir;
        else
            flag = false;
        end
    end
    if fVerbose && ~flag
        fprintf(2, 'File does not exist: %s\n', vcFile);
    end
    end %func
    
