const express = require('express');
const path = require('path');

const MountainClient = require('./mountainclient-js').MountainClient;

let mt = new MountainClient();
mt.configDownloadFrom(['spikeforest.public']);

const app = express();

// Serve the static files from the React app
app.use(express.static(path.join(__dirname, '/../client/dist')));

// // An api endpoint that returns a short list of items
// app.get('/api/getList', (req,res) => {
//     var list = ["item1", "item2", "item3"];
//     res.json(list);
//     console.log('Sent list of items');
// });

// Load object
app.get("/api/loadObject", async (req, res) => {
    let path = decodeURIComponent(req.query.path)

    let obj = await mt.loadObject(path);
    if (obj) {
        res.send({ success: true, object: obj });
    }
    else {
        res.send({ success: false });
    }
});
// Load text
app.get("/api/loadText", async (req, res) => {
    let path = decodeURIComponent(req.query.path)

    let txt = await mt.loadText(path);
    if (txt) {
        res.send({ success: true, text: txt });
    }
    else {
        res.send({ success: false });
    }
});
// Find file
app.get("/api/findFile", async (req, res) => {
    let path = decodeURIComponent(req.query.path)

    let url = await mt.findFile(path);
    if (url) {
        res.send({ success: true, url: url });
    }
    else {
        res.send({ success: false });
    }
});

// Handles any requests that don't match the ones above
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname + '/../client/dist/index.html'));
});

const port = process.env.PORT || 5000;
app.listen(port);

console.log(`App is listening on port ${port}`);