const MountainClient = require('../mountainclient-js').MountainClient;

const STATUS_WAITING = 'waiting';
const STATUS_CONNECTED = 'connected';
const STATUS_NOT_CONNECTED = 'not_connected';
const STATUS_UNKNOWN = 'unknown';

class KacheryConnection {
    constructor(kacheryName) {
        this._kacheryName = kacheryName;
        this._connectionStatus = STATUS_WAITING;
        this._enabled = true;
    }
    get kacheryName() {
        return this._kacheryName;
    }
    get connectionStatus() {
        return this._connectionStatus;
    }
    get enabled() {
        return this._enabled;
    }
    set enabled(val) {
        this._enabled = val;
    }
    resetStatus() {
        this._connectionStatus = STATUS_WAITING;
    }
    async checkConnection(mt) {
        let ok = await mt.probeKachery(this.kacheryName);
        this._connectionStatus = ok ? STATUS_CONNECTED : STATUS_NOT_CONNECTED;
    }
}

export default class KacheryManager {
    _connections = [
    ];
    _localStorageConfigKey = null;
    _localStorageCacheManager = new LocalStorageCacheManager();
    _localStorageCacheEnabled = true;
    addConnection(name) {
        let newc = new KacheryConnection(name);
        this._connections.push(newc);
        this.saveConfigToLocalStorage();
        return newc;
    }
    addSystemConnection(name, opts) {
        if (!this.connection(name)) {
            let cc = this.addConnection(name);
            cc.enabled = opts.enabledByDefault || false;
        }
        this.saveConfigToLocalStorage();
    }
    setConnectionEnabled(name, val) {
        let cc = this.connection(name);
        if (!cc) return;
        cc.enabled = val;
        this.saveConfigToLocalStorage();
    }
    removeConnection(name) {
        let newConnections = [];
        for (let c of this._connections) {
            if (c.kacheryName !== name)
                newConnections.push(c);
        }
        this._connections = newConnections;
        this.saveConfigToLocalStorage();
    }
    allConnections() {
        return this._connections;
    }
    connection(name) {
        for (let c of this._connections) {
            if (c.kacheryName === name)
                return c;
        }
        return null;
    }

    pairioConnectionStatus() {
        return STATUS_UNKNOWN;
    }
    setLocalStorageConfigKey(key) {
        this._localStorageConfigKey = key;
        this._loadConfigFromLocalStorage();
    }
    enabledKacheryNames() {
        return this._connections
            .filter((kc) => (kc.enabled === true))
            .map((kc) => (kc.kacheryName));
    }
    localStorageCacheEnabled() {
        return this._localStorageCacheEnabled;
    }
    setLocalStorageCacheEnabled(val) {
        this._localStorageCacheEnabled = val;
        this.saveConfigToLocalStorage();
    }
    localStorageCacheManager() {
        return this._localStorageCacheManager;
    }
    electronFileSystemAccessEnabled() {
        return this._electronFileSystemAccessEnabled;
    }
    setElectronFileSystemAccessEnabled(val) {
        this._electronFileSystemAccessEnabled = val;
        this.saveConfigToLocalStorage();
    }
    newMountainClient() {
        if ((window.electron_new_mountainclient) && (this._electronFileSystemAccessEnabled)) {
            return window.electron_new_mountainclient();
        }
        else {
            return new MountainClient();
        }
    }
    async checkAllConnections() {
        let mt = this.newMountainClient();
        for (let kc of this._connections) {
            await kc.checkConnection(mt);
        }
    }
    async checkWaitingConnections() {
        let mt = this.newMountainClient();
        for (let kc of this._connections) {
            if (kc.connectionStatus === STATUS_WAITING)
                await kc.checkConnection(mt);
        }
    }
    async loadDirectory(path) {
        let X;
        if (path.startsWith('key://')) {
            let mt = this.newMountainClient();
            mt.configDownloadFrom(this.enabledKacheryNames());
            path = await mt.resolveKeyPath(path);
            if (!path) return null;
        }
        if (path.startsWith('sha1dir://')) {
            let vals = path.split('/');
            vals[2] = vals[2].split('.')[0];
            X = await this.loadObject(`sha1://${vals[2]}`);
            if (!X) return null;
            for (let i = 3; i < vals.length; i++) {
                if (vals[i]) {
                    if ((X.dirs) && (vals[i] in X.dirs)) {
                        X = X.dirs[vals[i]];
                    }
                    else {
                        return null;
                    }
                }
            }
        }
        else {
            return null;
        }

        return X;
    }
    async loadObject(path, opts) {
        let txt = await this.loadText(path, opts);
        if (!txt) return;
        let obj;
        try {
            obj = JSON.parse(txt);
        }
        catch (err) {
            console.info(txt);
            console.error(err);
            console.error(`Error parsing text in loadObject for ${path}`);
            return null;
        }
        return obj;
    }
    async loadText(path, opts) {
        if (path.startsWith('sha1://') || (path.startsWith('sha1dir://'))) {
            if (this._localStorageCacheEnabled) {
                let txt1 = this._localStorageCacheManager.loadText(path, opts);
                if (txt1) {
                    return txt1;
                }
            }
        }
        let mt = this.newMountainClient();
        mt.configDownloadFrom(this.enabledKacheryNames());
        let txt2 = await mt.loadText(path, {});
        if (path.startsWith('sha1://') || (path.startsWith('sha1dir://'))) {
            if (this._localStorageCacheEnabled) {
                if (txt2) {
                    this._localStorageCacheManager.saveText(path, txt2);
                }
            }
        }
        return txt2;
    }
    saveConfigToLocalStorage() {
        let obj = {
            kacheryConnections: []
        };
        for (let cc of this._connections) {
            obj.kacheryConnections.push({
                kacheryName: cc.kacheryName,
                enabled: cc.enabled
            });
        }
        obj.localStorageCacheEnabled = this._localStorageCacheEnabled;
        obj.electronFileSystemAccessEnabled = this._electronFileSystemAccessEnabled;
        localStorage.setItem(this._localStorageConfigKey, JSON.stringify(obj));
    }
    _loadConfigFromLocalStorage() {
        if (!this._localStorageConfigKey)
            return;

        let obj;
        try {
            obj = JSON.parse(localStorage.getItem(this._localStorageConfigKey)) || {};
        }
        catch (err) {
            obj = {};
        }
        let ccc = obj.kacheryConnections || [];
        for (let cc of ccc) {
            if (cc.kacheryName) {
                let cc0 = this.addConnection(cc.kacheryName);
                cc0.enabled = cc.enabled || false;
            }
        }
        if ('localStorageCacheEnabled' in obj) {
            this._localStorageCacheEnabled = obj.localStorageCacheEnabled;
        }
        else {
            this._localStorageCacheEnabled = true;
        }
        if ('electronFileSystemAccessEnabled' in obj) {
            this._electronFileSystemAccessEnabled = obj.electronFileSystemAccessEnabled;
        }
        else {
            this._electronFileSystemAccessEnabled = true;
        }
    }
}

class LocalStorageCacheManager {
    loadText(path) {
        let p = this._canonicalPath(path);
        let txt = localStorage.getItem('cache.' + p);
        if (!txt) return null;
        console.info(`Retrieved from local storage: ${p}`);
        return txt;
    }
    saveText(path, txt) {
        if (txt.length < 1e5) {
            let p = this._canonicalPath(path);
            localStorage.setItem('cache.' + p, txt);
        }
    }
    totalBytesUsed() {
        var bytesTotal = 0;
        for (let x in localStorage) {
            if (x.startsWith('cache.')) {
                let xLen = (((localStorage[x].length || 0) + (x.length || 0)) * 2);
                bytesTotal += xLen;
            }
        };
        return bytesTotal;
    }
    clear() {
        for (let x in localStorage) {
            if (x.startsWith('cache.')) {
                localStorage.removeItem(x);
            }
        };
    }
    _canonicalPath(path) {
        if (path.startsWith('sha1://')) {
            let vals = path.split('/');
            return `sha1://${vals[2]}`;

        }
        else {
            return path;
        }
    }
}