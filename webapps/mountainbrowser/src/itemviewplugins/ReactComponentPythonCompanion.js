const stable_stringify = require('json-stable-stringify');

class CompanionProcess {
    constructor(pythonCode) {
        this._pythonState = {};
        this._javaScriptState = {};
        this._receiveMessageHandlers = [];
        this._process = new window.ProcessRunner(pythonCode);
        this._process.onReceiveMessage(this._handleProcessMessage);
    }

    sendMessage(msg) {
        this._process.sendMessage(msg);
    }
    close() {
        this._process.close();
    }
    onReceiveMessage(handler) {
        this._receiveMessageHandlers.push(handler);
    }
    _handleProcessMessage = (msg) => {
        this._receiveMessageHandlers.forEach((handler) => {
            handler(msg);
        })
    }
}

class ReactComponentPythonCompanion {
    constructor(component, pythonCode) {
        this._component = component;
        this._pythonCode = pythonCode;
        this._pythonState = {};
        this._javaScriptState = {};
        this._process = null;
        this._pendingJavaScriptState = {};
        this._syncPythonStateToStateKeys = [];
    }

    syncPythonStateToState(keys) {
        this._syncPythonStateToStateKeys.push(...keys);
    }

    start() {
        if (this._process) return;
        this._process = new CompanionProcess(this._pythonCode);
        this._process.onReceiveMessage(this._handleReceiveMessageFromProcess);
        window.addEventListener('beforeunload', this._cleanup);
        if (Object.keys(this._pendingJavaScriptState).length > 0) {
            this.setJavaScriptState(this._pendingJavaScriptState);
            this._pendingJavaScriptState = {};
        }
    }

    stop() {
        this._cleanup();
        window.removeEventListener('beforeunload', this._cleanup); // remove the event handler for normal unmounting
    }

    _cleanup() {
        if (!this._process) return;
        this._process.close();
        this._process = null;
    }

    setJavaScriptState = (state) => {
        if (!this._process) {
            for (let key in state) {
                this._pendingJavaScriptState[key] = state[key];
            }
            return;
        }
        let newJavaScriptState = {};
        for (let key in state) {
            if (!compare(state[key], this._javaScriptState[key])) {
                this._javaScriptState[key] = clone(state[key]);
                newJavaScriptState[key] = clone(state[key]);
            }
        }
        if (Object.keys(newJavaScriptState).length > 0) {
            this._process.sendMessage({
                name: 'setJavaScriptState',
                state: newJavaScriptState
            });
        }
    }

    getJavaScriptState(key) {
        if (key in this._javaScriptState) {
            return JSON.parse(JSON.stringify(this._javaScriptState[key]));
        }
        else return undefined;
    }

    getPythonState(key) {
        if (key in this._pythonState) {
            return JSON.parse(JSON.stringify(this._pythonState[key]));
        }
        else return undefined;
    }

    _handleReceiveMessageFromProcess = (msg) => {
        if (msg.name == 'setPythonState') {
            let somethingChanged = false;
            for (let key in msg.state) {
                if (!compare(msg.state[key], this._pythonState[key])) {
                    this._pythonState[key] = clone(msg.state[key]);
                    somethingChanged = true;
                }
            }
            if (somethingChanged) {
                this._copyPythonStateToState(this._syncPythonStateToStateKeys);
            }
        }
    }

    _copyPythonStateToState(keys) {
        let newState = {};
        for (let key of keys) {
            if (!compare(this._pythonState[key], this._component.state[key])) {
                newState[key] = clone(this._pythonState[key]);
            }
        }
        this._component.setState(newState);
    }
}

function compare(a, b) {
    if ((a === undefined) && (b === undefined))
        return true;
    if ((a === null) && (b === null))
        return true;
    return (stable_stringify(a) === stable_stringify(b));
}

function clone(a) {
    if (a === undefined)
        return undefined;
    if (a === null)
        return null;
    return JSON.parse(stable_stringify(a));
}

export default ReactComponentPythonCompanion;