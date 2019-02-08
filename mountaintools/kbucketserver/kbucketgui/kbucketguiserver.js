var express = require('express');

var app = express();
app.set('port', (process.env.PORT || 5082));
app.use(express.static(__dirname+'/web'));

app.listen(app.get('port'), function() {
	console.info('kbucketgui is running on port:: '+app.get('port'), {port:app.get('port')});
});

