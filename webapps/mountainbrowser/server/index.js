var express = require('express');
var app = express();

//setting middleware
app.use(express.static(__dirname + '/../dist'));


const port = process.env.PORT || 6060;
app.listen(port);
console.info(`MountainBrowser server is listening on port ${port}`);