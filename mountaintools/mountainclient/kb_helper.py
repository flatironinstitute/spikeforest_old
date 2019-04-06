from .mountainclient import client as mt
import sys
import os

def _kb_ls_helper(path, _cat=False, _dest=None):
    if mt.isFile(path):
        path2 = path2 = mt.realizeFile(path=path)
        if path2:
            if _cat:
                _cat_file(path2)
            elif _dest:
                _copy_file(path2, _dest)
            else:
                print(os.path.basename(path))
            exit(0)
        else:
            print('Problem realizing file.')
            exit(-1)

    # case of a directory (or not found)
    dd = mt.readDir(path, recursive=False, include_sha1=False)
    if not dd:
        print('Not found.')
        exit(-1)
    
    if _cat:
        print('Cannot cat a directory.')
        exit(-1)

    if _dest:
        if _realize_directory_from_dd(dd, _dest):
            exit(0)
        else:
            print('Problem realizing directory.')
            exit(-1)

    for fname in dd['files'].keys():
        print(fname)
    for dname in dd['dirs'].keys():
        print(dname)

def _realize_directory_from_dd(dd, dst_path):
    if os.path.exists(dst_path):
        print('File or directory already exists: '+dst_path)
        return False
    os.makedirs(dst_path)
    for fname, obj in dd['files'].items():
        sha1 = obj['sha1']
        if not mt.realizeFile(path='sha1://'+sha1, dest_path=os.path.join(dst_path, fname)):
            print('Unable to realize file: '+os.path.join(dst_path, fname))
            return False
    for dname, obj in dd['dirs'].items():
        if not _realize_directory_from_dd(obj, os.path.join(dst_path, dname)):
            return False
    return True
        

def _cat_file(path):
    path2 = mt.realizeFile(path)
    if not path2:
        print('Unable to realize file.')
        exit(-1)

    with open(path2,'rb') as f:
        while True:
            data = os.read(f.fileno(), 4096)
            if len(data) == 0:
                break
            os.write(sys.stdout.fileno(), data)

def _copy_file(path, dest_path):
    if not mt.realizeFile(path, dest_path=dest_path, show_progress=True):
        print('Unable to realize file.')
        exit(-1)