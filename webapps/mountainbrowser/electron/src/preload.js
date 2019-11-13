window.using_electron = true;

const MountainClient = require('../../src/mountainclient-js').MountainClient;
const { spawn } = require('child_process');

const util = require('util');
const exec = util.promisify(require('child_process').exec);
const fs = require('fs');
const path = require('path');
const tmp = require('tmp');

window.electron_new_mountainclient = function () {
    return new MountainClient({ fs: fs });
}

window.ProcessRunner = function (pythonCode) {
    let tmpDir = tmp.dirSync({ template: 'tmp-mountainbrowser-XXXXXX', unsafeCleanup: true});;
    let exePath = tmpDir.name + '/entry.py';
    fs.writeFileSync(exePath, pythonCode);

    let m_process = spawn('python', [exePath]);
    m_process.stderr.on('data', (data) => {
        console.error('FROM PROCESS:', data.toString());
    });
    let m_buf = '';
    this.sendMessage = function (msg) {
        m_process.stdin.write(JSON.stringify(msg) + '\n');
    }
    this.onReceiveMessage = function (handler) {
        m_process.stdout.on('data', (data) => {
            m_buf = m_buf + data.toString();
            while (true) {
                let ind = m_buf.indexOf('\n');
                if (ind >= 0) {
                    let txt = m_buf.slice(0, ind);
                    m_buf = m_buf.slice(ind + 1);
                    let msg = JSON.parse(txt);
                    handler(msg);
                }
                else {
                    break;
                }
            }
        });
    }
    this.close = function() {
        // remove the temporary directory
        if (fs.existsSync(tmpDir.name)) {
            //removeDir(dirPath.name);
            tmpDir.removeCallback();
        }
        this.sendMessage({name: "quit"});
    }
}

// function removeDir(dirPath) {
//     if (fs.existsSync(dirPath)) {
//         return;
//     }

//     var list = fs.readdirSync(dirPath);
//     for (var i = 0; i < list.length; i++) {
//         var filename = path.join(dirPath, list[i]);
//         var stat = fs.statSync(filename);

//         if (filename == "." || filename == "..") {
//             // do nothing for current and parent dir
//         } else if (stat.isDirectory()) {
//             removeDir(filename);
//         } else {
//             fs.unlinkSync(filename);
//         }
//     }

//     fs.rmdirSync(dirPath);
// };

window.executeJob = async function (job, input, opts) {
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
    catch (err) {
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