function p_kilosort2(kilosort_src, ironclust_src, temp_path, raw_fname, geom_fname, firings_out_fname, arg_fname)
% cmdstr2 = sprintf("p_ironclust('$(tempdir)','$timeseries$','$geom$','$firings_out$','$(argfile)');");

if exist(temp_path, 'dir') ~= 7
    mkdir(temp_path);
end

% prepare for kilosort execution
addpath(genpath(kilosort_src));
addpath(fullfile(ironclust_src, 'matlab'), fullfile(ironclust_src, 'matlab/mdaio'), fullfile(ironclust_src, 'matlab/npy-matlab'));    
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
writemda(mr_out', firings_out_fname, 'float32');
end %func


%--------------------------------------------------------------------------
function ops = import_ksort_(raw_fname, geom_fname, arg_fname, fpath)
% fpath: output path
S_txt = irc('call', 'meta2struct', {arg_fname});
[spkTh, useGPU] = deal(-abs(S_txt.detect_threshold), 1);

% convert to binary file (int16)
fbinary = strrep(raw_fname, '.mda', '.bin');
[Nchannels, ~] = mda2bin_(raw_fname, fbinary, S_txt.detect_sign);

% create a probe file
mrXY_site = csvread(geom_fname);
vcFile_chanMap = fullfile(fpath, 'chanMap.mat');
createChannelMapFile_(vcFile_chanMap, Nchannels, mrXY_site(:,1), mrXY_site(:,2));

ops = config_kilosort2_(fpath, fbinary, vcFile_chanMap, spkTh, useGPU, S_txt.samplerate); %obtain ops

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
function S_chanMap = createChannelMapFile_(vcFile_channelMap, Nchannels, xcoords, ycoords, shankInd)
if nargin<6, shankInd = []; end

connected = true(Nchannels, 1);
chanMap   = 1:Nchannels;
chanMap0ind = chanMap - 1;

xcoords   = xcoords(:);
ycoords   = ycoords(:);

if isempty(shankInd)
    shankInd   = ones(Nchannels,1); % grouping of channels (i.e. tetrode groups)
end
[~, name, ~] = fileparts(vcFile_channelMap);
S_chanMap = makeStruct_(chanMap, connected, xcoords, ycoords, shankInd, chanMap0ind, name);
save(vcFile_channelMap, '-struct', 'S_chanMap')
end %func


%--------------------------------------------------------------------------
% convert mda to int16 binary format, flip polarity if detect sign is
% positive
function [nChans, nSamples] = mda2bin_(raw_fname, fbinary, detect_sign)

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


%--------------------------------------------------------------------------
function ops = config_kilosort2_(fpath, fbinary, vcFile_chanMap, spkTh, useGPU, sRateHz)

% rootH = '~/kilosort';
ops.fproc       = fullfile(fpath, 'temp_wh.dat'); % proc file on a fast SSD  ;
ops.trange = [0 Inf]; % time range to sort
ops.NchanTOT    = numel(a.chanMap); % total number of channels in your recording

% the binary file is in this folder
ops.fbinary = fbinary;

ops.chanMap = vcFile_chanMap;
% ops.chanMap = 1:ops.Nchan; % treated as linear probe if no chanMap file

% sample rate
ops.fs = sRateHz;  

% frequency for high pass filtering (150)
ops.fshigh = 150;   

% minimum firing rate on a "good" channel (0 to skip)
ops.minfr_goodchannels = 0.1; 

% threshold on projections (like in Kilosort1, can be different for last pass like [10 4])
ops.Th = [10 4];  

% how important is the amplitude penalty (like in Kilosort1, 0 means not used, 10 is average, 50 is a lot) 
ops.lam = 10;  

% splitting a cluster at the end requires at least this much isolation for each sub-cluster (max = 1)
ops.AUCsplit = 0.9; 

% minimum spike rate (Hz), if a cluster falls below this for too long it gets removed
ops.minFR = 1/50; 

% number of samples to average over (annealed from first to second value) 
ops.momentum = [20 400]; 

% spatial constant in um for computing residual variance of spike
ops.sigmaMask = 30; 

% threshold crossings for pre-clustering (in PCA projection space)
ops.ThPre = 8;

% danger, changing these settings can lead to fatal errors
% options for determining PCs
ops.spkTh           = spkTh;      % spike threshold in standard deviations (-6)
ops.reorder         = 1;       % whether to reorder batches for drift correction. 
ops.nskip           = 25;  % how many batches to skip for determining spike PCs

ops.GPU                 = useGPU; % has to be 1, no CPU version yet, sorry
% ops.Nfilt               = 1024; % max number of clusters
ops.nfilt_factor        = 4; % max number of clusters per good channel (even temporary ones)
ops.ntbuff              = 64;    % samples of symmetrical buffer for whitening and spike detection
ops.NT                  = 64*1024+ ops.ntbuff; % must be multiple of 32 + ntbuff. This is the batch size (try decreasing if out of memory). 
ops.whiteningRange      = 32; % number of channels to use for whitening each channel
ops.nSkipCov            = 25; % compute whitening matrix from every N-th batch
ops.scaleproc           = 200;   % int16 scaling of whitened data
ops.nPCs                = 3; % how many PCs to project the spikes into
ops.useRAM              = 0; % not yet available

end %func



