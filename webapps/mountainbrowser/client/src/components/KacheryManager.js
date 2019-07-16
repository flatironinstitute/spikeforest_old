const MountainClient = require('@mountainclient-js').MountainClient;

const STATUS_WAITING = 'waiting';
const STATUS_CONNECTED = 'connected';
const STATUS_NOT_CONNECTED = 'not_connected';
const STATUS_UNKNOWN = 'unknown';

class KacheryConnection {
    constructor(kacheryName) {
        this._kacheryName = kacheryName;
        this._connectionStatus = STATUS_WAITING;
    }
    get kacheryName() {
        return this._kacheryName;
    }
    get connectionStatus() {
        return this._connectionStatus;
    }
    resetStatus() {
        this._connectionStatus = STATUS_WAITING;
    }
    async checkConnection() {
        let mt = new MountainClient();
        let ok = await mt.probeKachery(this.kacheryName);
        this._connectionStatus = ok ? STATUS_CONNECTED : STATUS_NOT_CONNECTED;
    }
}

export default class KacheryManager {
    _connections = [
    ];
    addConnection(name) {
        this._connections.push(
            new KacheryConnection(name)
        );
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
    async checkAllConnections() {
        for (let kc of this._connections) {
            await kc.checkConnection();
        }
    }
    async checkWaitingConnections() {
        for (let kc of this._connections) {
            if (kc.connectionStatus === STATUS_WAITING)
                await kc.checkConnection();
        }
    }
}
