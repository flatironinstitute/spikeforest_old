exports.KBNodeConfig = KBNodeConfig;

const fs = require('fs');

const keypair = require('keypair');
const async = require('async');
const user_settings = require('user-settings').file('.kbucket-settings');
const inquirer = require('inquirer');
const email_validator = require('email-validator');
const sha1 = require('node-sha1');

// kbnode type = hub or share
function KBNodeConfig(kbnode_directory) {
  const that = this;
  this.configDir = function() {
    return m_config_dir;
  };
  this.configDirExists = function() {
    return fs.existsSync(m_config_dir);
  };
  this.createNew = function(kbnode_type, opts, callback) {
    createNew(kbnode_type, opts, callback);
  };
  this.generatePemFilesAndId =function(opts,callback) {
    generate_pem_files_and_kbnode_id(opts,callback);
  };
  this.initialize = function(callback) {
    initialize(callback);
  };
  this.runInteractiveConfiguration = function(opts, callback) {
    runInteractiveConfiguration(opts, callback);
  };
  this.kbNodeId = function() {
    return m_kbnode_id;
  };
  this.kbNodeType = function() {
    return m_kbnode_type;
  };
  this.kbNodeDirectory = function() {
    return kbnode_directory;
  };
  this.getPrvFromCache = function(relpath) {
    return get_prv_from_cache(relpath);
  };
  this.savePrvToCache = function(relpath, prv) {
    return save_prv_to_cache(relpath, prv);
  };
  this.publicKey = function() {
    return publicKey();
  };
  this.privateKey = function() {
    return privateKey();
  };
  this.getConfig = function(key) {
    return get_config(key);
  };
  this.setListenPort = function(port) {
    m_listen_port = port;
  };
  this.listenPort = function() {
    return m_listen_port;
  };
  this.listenUrl = function() {
    return listen_url();
  };
  this.topHubUrl = function() {
    return m_top_hub_url || listen_url();
  };
  this.setTopHubUrl = function(url) {
    if (url != m_top_hub_url) {
      m_top_hub_url = url;
      for (var i in m_on_top_hub_url_changed_handlers)
        m_on_top_hub_url_changed_handlers[i]();
    }
  };
  this.onTopHubUrlChanged = function(handler) {
    m_on_top_hub_url_changed_handlers.push(handler);
  };
  this.getNodeInfo = function() {
    return getNodeInfo();
  };
  this.incrementMetric = function(name, increment) {
    if (increment===undefined) increment=1;
    m_metrics[name] = (m_metrics[name] || 0) + increment;
    schedule_write_metrics();
  };
  this.metrics = function() {
    return m_metrics;
  };

  var m_config_dir = kbnode_directory + '/.kbucket';
  var m_config_file_path = m_config_dir + '/kbnode.json';
  var m_kbnode_id = ''; //set by initialize
  var m_kbnode_type = ''; //set by initialize
  var m_listen_port = 0;
  var m_top_hub_url = '';
  var m_on_top_hub_url_changed_handlers = [];
  var m_metrics = {};

  function createNew(kbnode_type, opts, callback) {
    if (!fs.existsSync(kbnode_directory)) {
      callback('Directory does not exist: ' + kbnode_directory);
      return;
    }
    if (!fs.statSync(kbnode_directory).isDirectory()) {
      callback('Not a directory: ' + kbnode_directory);
      return;
    }
    if (fs.existsSync(kbnode_directory + '/.kbucket')) {
      callback(`Cannot create new ${kbnode_type}. File or directory .kbucket already exists.`);
      return;
    }
    fs.mkdirSync(kbnode_directory + '/.kbucket');
    set_config('kbnode_type', kbnode_type);
    callback(null);
  }

  function initialize(callback) {
    if (!fs.existsSync(kbnode_directory)) {
      callback('Directory does not exist: ' + kbnode_directory);
      return;
    }
    if (!fs.statSync(kbnode_directory).isDirectory()) {
      callback('Not a directory: ' + kbnode_directory);
      return;
    }

    m_kbnode_id = get_config('kbnode_id');
    m_kbnode_type = get_config('kbnode_type');

    if ((!m_kbnode_id) || (!m_kbnode_type)) {
      callback('Invalid kbnode.');
      return;
    }

    if (m_kbnode_type == 'share') {
      if (!require('fs').existsSync(m_config_dir + '/prv_cache')) {
        require('fs').mkdirSync(m_config_dir + '/prv_cache');
      }
    }

    async.series([init_step1],
      function() {
        callback(null);
      }
    );

    function init_step1(cb) {
      start_the_cleaner();
      cb();
    }
  }

  function runInteractiveConfiguration(opts, callback) {
    var questions = [];
    if (!opts.clone_only) {
      questions.push({
        type: 'input',
        name: 'name',
        message: `Name for this KBucket ${m_kbnode_type}:`,
        default: get_config('name') || require('path').basename(kbnode_directory),
        validate: is_valid_kbnode_name
      });
      var str;
      if (m_kbnode_type == 'hub') {
        str = 'Are you hosting this hub for scientific research purposes (yes/no)?';
      } else if (m_kbnode_type == 'share') {
        str = 'Are sharing this data for scientific research purposes (yes/no)?';
      } else {
        console.error('Unexpected kbnode type: ' + m_kbnode_type);
        process.exit(-1);
      }
      questions.push({
        type: 'input',
        name: 'scientific_research',
        message: str,
        default: get_config('scientific_research') || '',
        validate: is_valid_scientific_research
      });
      questions.push({
        type: 'input',
        name: 'description',
        message: `Brief description of this KBucket ${m_kbnode_type}:`,
        default: get_config('description') || '',
        validate: is_valid_description,
        optional:false
      });
      questions.push({
        type: 'input',
        name: 'owner',
        message: 'Owner\'s name (i.e., your full name):',
        default: get_config('owner') || user_settings.get('default_owner') || '',
        validate: is_valid_owner
      });
      questions.push({
        type: 'input',
        name: 'owner_email',
        message: 'Owner\'s email (i.e., your email):',
        default: get_config('owner_email') || user_settings.get('default_owner_email') || '',
        validate: is_valid_email
      });
      if (m_kbnode_type == 'share') {
        questions.push({
          //type: 'list',
          type: 'input',
          name: 'confirm_share',
          message: `Share all data recursively contained in the directory ${kbnode_directory}? (yes/no)`,
          //choices: ['yes', 'no'],
          default: get_config('confirm_share') || '',
        });
        questions.push({
          type: 'input',
          name: 'listen_url',
          message: 'Listen url for this hub (use . for http://localhost:[port]):',
          default: get_config('listen_url') || '.',
          validate: is_valid_url
        });
        questions.push({
          type: 'input',
          name: 'parent_hub_url',
          message: 'Connect to hub:',
          default: get_config('parent_hub_url') || 'https://kbucket.flatironinstitute.org',
          //default: get_config('parent_hub_url') || 'https://kbucket.org',
          validate: is_valid_url
        });
      }
      if (m_kbnode_type == 'hub') {
        questions.push({
          type: 'input',
          name: 'listen_port',
          message: 'Listen port for this hub:',
          default: get_config('listen_port') || 3240,
          validate: is_valid_port
        });
        questions.push({
          type: 'input',
          name: 'listen_url',
          message: 'Listen url for this hub (use . for http://localhost:[port]):',
          default: get_config('listen_url') || '.',
          validate: is_valid_url
        });
        questions.push({
          type: 'input',
          name: 'parent_hub_url',
          message: 'Parent hub url (use . for none):',
          default: get_config('parent_hub_url') || 'https://kbucket.flatironinstitute.org',
          //default: get_config('parent_hub_url') || 'https://kbucket.org',
          validate: is_valid_url
        });
      }
    } else {
      //clone only
      set_config('readonly', true);
      set_config('kbnode_type', opts.info.kbnode_type||opts.info.node_type);
      set_config('name', opts.info.name);
      set_config('description', opts.info.description);
      set_config('owner', opts.info.owner);
      set_config('owner_email', opts.info.owner_email);
      if (opts.kbshare_subdirectory) {
        set_config('subdirectory', opts.kbshare_subdirectory);
      }
    }

    if (opts.auto_use_defaults) {
      for (var i in questions) {
        var qq = questions[i];
        if (qq.default) {
          set_config(qq.name, qq.default);
        } else {
          if (!qq.optional) {
            console.error('Aborting due to missing required field: '+qq.name);
            process.exit(-1);
          };
        }
      }
      callback();
      return;
    }

    inquirer.prompt(questions)
      .then(function(answers) {
        for (var i in questions) {
          var qq = questions[i];
          set_config(qq.name, answers[qq.name]);
        }
        if ('owner' in answers)
          user_settings.set('default_owner', answers.owner);
        if ('owner_email' in answers)
          user_settings.set('default_owner_email', answers.owner_email);
        callback();
      });
  }

  function is_valid_kbnode_name(str) {
    if (str.length == 0) {
      return 'Name must not be empty.';
    }
    if (str.length > 100) {
      return 'Name is too long.';
    }
    return true;
  }

  function is_valid_scientific_research(str) {
    if (str == 'yes') {
      return true;
    } else if (str == 'no') {
      console.info('');
      console.info('KBucket should only be used to share data for scientific research purposes.');
      process.exit(-1);
      //return 'kbucket should only be used to share data used for scientific research'
    } else {
      return 'Invalid string: ' + str;
    }
  }

  function is_valid_description(str) {
    if (str.length > 1000) {
      return 'Description is too long.';
    }
    return true;
  }

  function is_valid_owner(str) {
    if (str.length == 0) {
      return 'Owner string must not be empty.';
    }
    if (str.length > 100) {
      return 'Owner string is too long.';
    }
    return true;
  }

  function is_valid_email(str) {
    if (!email_validator.validate(str)) {
      return 'Invalid email.';
    }
    return true;
  }

  function is_valid_url(str) {
    if (!str) return true; //a hack
    if (str == '.') return true; //a hack
    if ((str.startsWith('http://')) || (str.startsWith('https://')))
      return true;
    return 'Invalid url.';
  }

  function is_valid_port(port) {
    return (Number(port) == port); // todo: improve this test
  }

  function listen_url() {
    var url = get_config('listen_url');
    if (url == '.') {
      url = `http://localhost:${m_listen_port}`;
    }
    return url;
  }

  function generate_pem_files_and_kbnode_id(opts, callback) {
    if (!opts.clone_only) {
      if (get_config('kbnode_id')) {
        callback('Cannot generate public/private keys because node id has already been set.');
        return;
      }
      var pair = keypair();
      var private_key = pair.private;
      var public_key = pair.public;
      write_text_file(m_config_dir + '/private.pem', private_key);
      write_text_file(m_config_dir + '/public.pem', public_key);
      var kbnode_id = sha1(public_key).slice(0, 12); //important
      set_config('kbnode_id', kbnode_id);
    } else {
      set_config('kbnode_id', opts.info.kbnode_id);
    }
    callback();
  }

  function get_config(key) {
    var config = read_json_file(m_config_file_path);
    if (!config) {
      console.warn('Problem reading or parsing configuration file: ' + m_config_file_path);
      config = {};
    }
    return config[key];
  }

  function set_config(key, val) {
    var config = read_json_file(m_config_file_path) || {};
    config[key] = val;
    if (!write_json_file(m_config_file_path, config)) {
      console.error('Unable to write to file: ' + m_config_file_path + '. Aborting.');
      process.exit(-1);
    }
  }

  function publicKey() {
    var public_key = read_text_file(m_config_dir + '/public.pem');
    //var list=public_key.split('\n');
    return public_key;
  }

  function privateKey() {
    var private_key = read_text_file(m_config_dir + '/private.pem');
    //var list=public_key.split('\n');
    return private_key;
  }

  function get_prv_cache_fname(path) {
    // used for kbnode_type='share'
    if (!path) return '';
    return m_config_dir + '/prv_cache/' + sha1(path).slice(0, 12) + '.json';
  }

  function get_prv_from_cache(relpath) {
    // used for kbnode_type='share'
    var cache_fname = get_prv_cache_fname(relpath);
    if (!require('fs').existsSync(cache_fname)) {
      return null;
    }
    var obj = read_json_file(cache_fname);
    if (!obj) return null;
    if (!prv_cache_object_matches_file(obj, kbnode_directory + '/' + relpath)) {
      return null;
    }
    return obj.prv;
  }

  function prv_cache_object_matches_file(obj, path) {
    // used for kbnode_type='share'
    if (!obj) return false;
    let stat0;
    try {
      stat0 = require('fs').statSync(path);
    } catch (err) {
      return false;
    }
    if (stat0.size != obj.size) {
      return false;
    }
    if (stat0.mtime + '' != obj.mtime) {
      return false;
    }
    if (!obj.prv) return false;
    return true;
  }

  function save_prv_to_cache(relpath, prv) {
    // used for kbnode_type='share'
    var cache_fname = get_prv_cache_fname(relpath);
    var stat0 = require('fs').statSync(kbnode_directory + '/' + relpath);
    var obj = {};
    obj.path = relpath;
    obj.size = stat0.size;
    obj.mtime = stat0.mtime + '';
    obj.prv = prv;
    write_json_file(cache_fname, obj);
  }

  function start_the_cleaner() {
    cleanup(function(err) {
      if (err) {
        console.error(err);
        console.error('Aborting');
        process.exit(-1);
        return;
      }
      setTimeout(start_the_cleaner, 1000);
    });
  }

  function cleanup(callback) {
    if (m_kbnode_type == 'share') {
      cleanup_prv_cache(function(err) {
        if (err) {
          callback(err);
          return;
        }
        callback(null);
      });
    } else {
      callback(null);
    }
  }

  function cleanup_prv_cache(callback) {
    // used for kbnode_type='share'
    var prv_cache_dir = m_config_dir + '/prv_cache';
    require('fs').readdir(prv_cache_dir, function(err, files) {
      if (err) {
        callback('Error in cleanup_prv_cache:readdir: ' + err.message);
        return;
      }
      async.eachSeries(files, function(file, cb) {
        cleanup_prv_cache_file(prv_cache_dir + '/' + file, function(err) {
          if (err) {
            callback(err);
            return;
          }
          cb();
        });
      });
    });
  }

  function cleanup_prv_cache_file(cache_filepath, callback) {
    // used for kbnode_type='share'
    var obj = read_json_file(cache_filepath);
    if (!obj) {
      safe_remove_file(cache_filepath);
      callback(null);
      return;
    }
    var relpath1 = obj.path;
    if (get_prv_cache_fname(relpath1) != cache_filepath) {
      safe_remove_file(cache_filepath);
      callback(null);
      return;
    }
    if (!prv_cache_object_matches_file(obj, kbnode_directory + '/' + relpath1)) {
      safe_remove_file(cache_filepath);
      callback(null);
      return;
    }
    callback(null);
  }

  function getNodeInfo() {
    var ret = {
      kbnode_id: that.kbNodeId(),
      kbnode_type: that.kbNodeType(),
      name: that.getConfig('name'),
      description: that.getConfig('description'),
      owner: that.getConfig('owner'),
      owner_email: that.getConfig('owner_email'),
      listen_url: that.listenUrl() || undefined,
      public_key: that.publicKey() || undefined
    };
    return ret;
  }

  function safe_remove_file(cache_filepath) {
    try {
      require('fs').unlinkSync(cache_filepath);
    } catch (err) {
      console.warn('Unable to remove file: ' + cache_filepath);
    }
  }

  let m_write_metrics_scheduled = false;

  function schedule_write_metrics() {
    if (m_write_metrics_scheduled) return;
    m_write_metrics_scheduled = true;
    setTimeout(function() {
      m_write_metrics_scheduled = false;
      do_write_metrics();
    }, 1000);
  }

  function do_write_metrics() {
    write_json_file(m_config_dir + '/metrics.json', m_metrics);
  }
}


/*
function run_command_and_read_stdout(cmd, callback) {
  var P;
  try {
    let args=cmd.split(' ');
    P = require('child_process').spawn(cmd[0],cmd.slice(1), {
      shell: false
    });
  } catch (err) {
    callback(`Problem launching ${cmd}: ${err.message}`);
    return;
  }
  var txt = '';
  P.stdout.on('data', function(chunk) {
    txt += chunk.toString();
  });
  P.on('close', function(code) {
    callback(null, txt);
  });
  P.on('error', function(err) {
    callback(`Problem running ${cmd}: ${err.message}`);
  })
}
*/

function parse_json(str) {
  try {
    return JSON.parse(str);
  } catch (err) {
    return null;
  }
}

function read_json_file(fname) {
  try {
    var txt = require('fs').readFileSync(fname, 'utf8');
    return parse_json(txt);
  } catch (err) {
    return null;
  }
}

function read_text_file(fname) {
  try {
    var txt = require('fs').readFileSync(fname, 'utf8');
    return txt;
  } catch (err) {
    return null;
  }
}

function write_text_file(fname, txt) {
  try {
    require('fs').writeFileSync(fname, txt);
    return true;
  } catch (err) {
    return false;
  }
}

function write_json_file(fname, obj) {
  try {
    require('fs').writeFileSync(fname, JSON.stringify(obj, null, 4));
    return true;
  } catch (err) {
    return false;
  }
}