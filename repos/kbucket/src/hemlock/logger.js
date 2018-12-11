const winston = require('winston');
//require('winston-daily-rotate-file');

exports.initialize = initialize;
exports.logger = logger;

var g_logger = winston.createLogger({
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  )
});

function initialize(opts) {

  if ((!opts.directory) || (!opts.application)) {
    console.warn('Problem initializing logger', opts);
    return;
  }
  if (!require('fs').existsSync(opts.directory)) {
    require('fs').mkdirSync(opts.directory);
  }

  {
    let transport=new winston.transports.File({ filename: `${opts.directory}/${opts.application}.error.log`, level: 'error' });
    g_logger.add(transport);
  }
  {
    let transport=new winston.transports.File({ filename: `${opts.directory}/${opts.application}.combined.log`});
    g_logger.add(transport);
  }


  /*
  transport = new(winston.transports.DailyRotateFile)({
    filename: `${opts.application}-%DATE%.log`,
    dirname: `${opts.directory}`,
    datePattern: 'YYYY-MM-DD-HH',
    zippedArchive: false,
    maxSize: '20m',
    maxFiles: 10
  });

  transport.on('rotate', function(oldFilename, newFilename) {
    //
  });

  g_logger.add(transport);
  */
}

function logger() {
  return g_logger;
}