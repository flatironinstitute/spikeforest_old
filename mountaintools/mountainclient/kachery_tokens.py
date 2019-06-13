import os
from typing import Optional, Iterable

class KacheryTokens(object):
    def __init__(self, path: Optional[str]=None):
        if path is None:
            path = os.path.join(os.environ.get('HOME', ''), '.mountaintools', 'kachery_tokens')
        self._path = path
        self._entries = []
        try:
            with open(self._path, 'r') as f: self._entries = f.read().splitlines()
        except:
            pass

    def add(self, name: str, type: str, token: str) -> bool:
        if not len(token):
            return False
        if type not in ['download', 'upload']:
            return False
        for i in range(0, len(self._entries)):
            current = self._entries[i]
            if current.startswith('#') or not len(current.strip()):
                continue
            entry = current.strip().split()
            if entry[0] == name and entry[1] == type:
                entry[2] = token
                self._entries[i] = '\t'.join(entry)
                return True
        # not found, let's add
        entry = [ name, type, token ]
        self._entries.append('\t'.join(entry))
        return True

    def add_download(self, name: str, token: str) -> bool:
        return self.add(name, 'download', token)
    
    def add_upload(self, name: str, token: str) -> bool:
        return self.add(name, 'upload', token)

    def disable(self, name: str, type: str):
        if not name or not type:
            return False
        if type not in ['download', 'upload']:
            return False
        for i in range(0, len(self._entries)):
            current = self._entries[i]
            if current.startswith('#') or not len(current.strip()):
                continue
            entry = current.strip().split()
            if entry[0] == name and entry[1] == type:
                self._entries[i] = '#'+self._entries[i]
                return True
        return False

    def enable(self, name: str, type: str) -> bool:
        if not name or not type:
            return False
        if type not in ['download', 'upload']:
            return False
        for i in range(0, len(self._entries)):
            current = self._entries[i]
            if not current.startswith('#'):
                continue
            entry = current[1:].strip().split()
            if len(entry) == 3 and entry[0] == name and entry[1] == type:
                self._entries[i] = current[1:].strip()
                return True
        return False

    def disable_download(self, name: str) -> bool:
        return self.disable(name, 'download')

    def disable_upload(self, name: str) -> bool:
        return self.disable(name, 'upload')

    def enable_download(self, name: str) -> bool:
        return self.enable(name, 'download')

    def enable_upload(self, name: str) -> bool:
        return self.enable(name, 'upload')

    def remove(self, name: str, type: Optional[str] = None) -> bool:
        if not type:
            dn = self.remove(name, 'download') 
            up = self.remove(name, 'upload')
            return dn or up
        if type not in ['download', 'upload']:
            return False
        for i in range(0, len(self._entries)):
            current = self._entries[i]
            if current.startswith('#') or not len(current.strip()):
                continue
            entry = current.strip().split()
            if entry[0] == name and entry[1] == type:
                del self._entries[i]
                return True
        return False

    def remove_download(self, name: str) -> bool:
        return self.remove(name, 'download')

    def remove_upload(self, name: str) -> bool:
        return self.remove(name, 'upload')

    def commit(self) -> None:
        if not os.path.exists(os.path.dirname(self._path)):
            os.makedirs(os.path.dirname(self._path))
        with open(self._path, 'w') as f:
            # strip empty lines from the end
            while len(self._entries) and not self._entries[0]: del self._entries[0]
            # save the rest
            for entry in self._entries:
                f.write(entry)
                f.write('\n')
    
    def entries(self) -> Iterable:
        for i in range(0, len(self._entries)):
            current = self._entries[i]
            if current.startswith('#') or not len(current.strip()):
                continue
            entry = current.strip().split()
            yield entry
