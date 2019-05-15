import random
import os
import tempfile
import hashlib
import json
import functools

def deprecated(reason):
    def decorator(func):
        if not func.__doc__: func.__doc__ = 'Deprecated'

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # TODO replace with warnings package
            print(reason)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def _db_load(path, *, count=0):
    if count > 10:
        raise Exception('Unexpected problem loading database file: ' + path)
    if os.path.exists(path):
        try:
            db_txt = _read_text_file(path)
        except:
            if os.path.exists(path):
                raise Exception('Unable to read database file: ' + path)
            else:
                return dict()
        try:
            db = json.loads(db_txt)
        except:
            if os.path.exists(path + '.save'):
                print('Warning: Problem parsing json in database file (restoring saved file): ' + path)
                try:
                    os.rename(path + '.save', path)
                except:
                    print('Warning: problem renaming .save file. Deleting')
                    try:
                        os.unlink(path + '.save')
                    except:
                        pass
                    try:
                        os.unlink(path)
                    except:
                        pass
            else:
                print('Warning: Problem parsing json in database file (deleting): ' + path)
                try:
                    os.unlink(path)
                except:
                    pass
            return _db_load(path, count=count + 1)
        return db
    else:
        return dict()


def _db_save(path, db):
    # create a backup first
    if os.path.exists(path):
        try:
            # make sure it is good before doing the backup
            _read_json_file(path)  # if not good, we get an exception
            if os.path.exists(path + '.save'):
                os.unlink(path + '.save')
            shutil.copyfile(path, path + '.save')
        except:
            # worst case, let's just proceed
            pass
    _write_json_file(db, path)

def _read_json_file(path):
    with open(path) as f:
        return json.load(f)


def _read_text_file(path):
    with open(path) as f:
        return f.read()


def _write_json_file(obj, path):
    with open(path, 'w') as f:
        return json.dump(obj, f)


def _write_text_file(fname, txt):
    with open(fname, 'w') as f:
        f.write(txt)

def _is_http_url(url):
    return url.startswith('http://') or url.startswith('https://')

def _sha1_of_string(txt):
    hh = hashlib.sha1(txt.encode('utf-8'))
    ret = hh.hexdigest()
    return ret


def _sha1_of_object(obj):
    txt = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(txt)


def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))

def _create_temporary_fname(ext):
    tempdir = os.environ.get('KBUCKET_CACHE_DIR', tempfile.gettempdir())
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    return tempdir + '/tmp_mountainclient_' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)) + ext
