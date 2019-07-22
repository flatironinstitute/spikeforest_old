window.using_electron = true;

console.log('----- preloading------');

const MountainClient = require('../../src/mountainclient-js').MountainClient;

const util = require('util');
const exec = util.promisify(require('child_process').exec);
const fs = require('fs');

window.electron_new_mountainclient = function() {
    return new MountainClient({fs: fs});
}

window.executeJob = async function(job, input, opts) {
    opts = opts || {};
    const job_fname = create_temporary_file();
    const input_fname = create_temporary_file();
    const result_fname = create_temporary_file();
    write_json_file(job_fname, job);
    write_json_file(input_fname, input);
    let cmd = `mt-execute-job ${job_fname} ${result_fname} --input ${input_fname}`;
    console.info(cmd);
    if (opts.download_from) {
        cmd = cmd + ` --download-from ${opts.download_from}`;
    }
    try {
        await exec(cmd);
    }
    catch(err) {
        console.error('Error executing job');
        console.error(err);
        cleanup();
        return null;
    }
    const result = read_json_file(result_fname);
    cleanup();
    return result;

    function cleanup() {
        if (fs.existsSync(job_fname))
            fs.unlinkSync(job_fname);
        if (fs.existsSync(input_fname))
            fs.unlinkSync(input_fname);
        if (fs.existsSync(result_fname))
            fs.unlinkSync(result_fname);
    }
}

function create_temporary_file() {
    return require('tmp').tmpNameSync();
}

function read_json_file(fname) {
    let txt = fs.readFileSync(fname, 'utf-8');
    return JSON.parse(txt);
}

function write_json_file(fname, obj) {
    fs.writeFileSync(fname, JSON.stringify(obj));
}