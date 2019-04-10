import subprocess
import tempfile
import shutil
import signal
import os
import time

class ShellScript():
    def __init__(self, script, script_path=None, keep_temp_files=False):
        lines = script.splitlines()
        lines = self._remove_initial_blank_lines(lines)
        if len(lines) > 0:
            num_initial_spaces = self._get_num_initial_spaces(lines[0])
            for ii, line in enumerate(lines):
                if len(line.strip()) > 0:
                    n = self._get_num_initial_spaces(line)
                    if n < num_initial_spaces:
                        print(script)
                        raise Exception('Problem in script. First line must not be indented relative to others')
                    lines[ii] = lines[ii][num_initial_spaces:]
        self._script = '\n'.join(lines)
        self._script_path = script_path
        self._keep_temp_files = keep_temp_files
        self._process = None
        self._files_to_remove = []
        self._dirs_to_remove = []
        self._start_time = None
        
    def __del__(self):
        self.cleanup()
        
    def substitute(self, old, new):
        self._script = self._script.replace(old, new)
        
    def write(self, script_path=None):
        if script_path is None:
            script_path = self._script_path
        if script_path is None:
            raise Exception('Cannot write script. No path specified')
        with open(script_path, 'w') as f:
            f.write(self._script)
        os.chmod(script_path, 0o744)
        
    def start(self):
        script_path = self._script_path
        if self._script_path is not None:
            script_path = self._script_path
        else:
            tempdir = tempfile.mkdtemp(prefix='tmp_shellscript')
            script_path = os.path.join(tempdir, 'script.sh')
            self._dirs_to_remove.append(tempdir)
        self.write(script_path)
        cmd = script_path
        print('RUNNING SHELL SCRIPT: ' + cmd)
        self._start_time = time.time()
        self._process = subprocess.Popen(cmd)
        
    def wait(self, timeout=None):
        if not self.isRunning():
            return self.returnCode()
        try:
            retcode = self._process.wait(timeout=timeout)
            return retcode
        except:
            return None
            
    def cleanup(self):
        if self._keep_temp_files:
            return
        for dirpath in self._dirs_to_remove:
            shutil.rmtree(dirpath)
            
    def stop(self):
        if not self.isRunning():
            return
        
        signals = [signal.SIGINT]*10 + [signal.SIGTERM]*10 + [signal.SIGKILL]*10
        
        for signal0 in signals:
            self._process.send_signal(signal0)
            try:
                self._process.wait(timeout=0.1)
                return
            except:
                pass
            
    def elapsedTimeSinceStart(self):
        if self._start_time is None:
            return
        return time.time() - self._start_time
        
    def isRunning(self):
        if not self._process:
            return False
        retcode = self._process.poll()
        if retcode is None:
            return True
        return False
    
    def isFinished(self):
        if not self._process:
            return False
        return not self.isRunning()
    
    def returnCode(self):
        if not self.isFinished():
            raise Exception('Cannot get return code before process is finished.')
        return self._process.returncode

    def scriptPath(self):
        return self._script_path
    
    def _remove_initial_blank_lines(self, lines):
        ii=0
        while ii < len(lines) and len(lines[ii].strip()) == 0:
            ii = ii + 1
        return lines[ii:]
    
    def _get_num_initial_spaces(self, line):
        ii = 0
        while ii < len(line) and line[ii] == ' ':
            ii = ii + 1
        return ii
