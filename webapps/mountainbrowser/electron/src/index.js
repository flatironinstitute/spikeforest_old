const {app, BrowserWindow} = require('electron');
const serve = require('electron-serve');

//const loadURL = serve({directory: __dirname + '/../../dist'});

let mainWindow;

(async () => {
	await app.whenReady();

	mainWindow = new BrowserWindow({
        webPreferences: {
            nodeIntegration: false,
            preload: __dirname + '/preload.js'
        }
    });

	// await loadURL(mainWindow);

	// // The above is equivalent to this:
	await mainWindow.loadURL('http://localhost:5050');
    // // The `-` is just the required hostname
    
    // mainWindow.webContents.openDevTools()
})();