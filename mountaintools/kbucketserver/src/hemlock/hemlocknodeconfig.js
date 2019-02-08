exports.HemlockNodeConfig = HemlockNodeConfig;

const fs = require('fs');

const keypair = require('keypair');
const async = require('async');
const user_settings = require('user-settings').file('.kbucket-settings');
const inquirer = require('inquirer');
const email_validator = require('email-validator');
const sha1 = require('node-sha1');

// hemlock_node type = hub or leaf
function HemlockNodeConfig(hemlock_node_directory, options) {
  const that = this;
  this.configDir = function() {
    return m_config_dir;
  };
  this.configDirExists = function() {
    return fs.existsSync(m_config_dir);
  };
  this.createNew = function(node_type, opts, callback) {
    createNew(node_type, opts, callback);
  };
  this.generatePemFilesAndId = function(opts, callback) {
    generate_pem_files_and_node_id(opts, callback);
  };
  this.initialize = function(callback) {
    initialize(callback);
  };
  this.runInteractiveConfiguration = function(opts, callback) {
    runInteractiveConfiguration(opts, callback);
  };
  this.hemlockNodeId = function() {
    return m_node_id;
  };
  this.hemlockNodeType = function() {
    return m_node_type;
  };
  this.hemlockNodeDirectory = function() {
    return hemlock_node_directory;
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
  this.setConfig = function(key, val) {
    return set_config(key, val);
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
    if (increment === undefined) increment = 1;
    m_metrics[name] = (m_metrics[name] || 0) + increment;
    schedule_write_metrics();
  };
  this.metrics = function() {
    return m_metrics;
  };

  var m_config_dir = hemlock_node_directory + '/' + options.config_directory_name;
  var m_config_file_path = m_config_dir + '/' + options.config_file_name;
  var m_node_id = ''; //set by initialize
  var m_node_type = ''; //set by initialize
  var m_listen_port = 0;
  var m_top_hub_url = '';
  var m_on_top_hub_url_changed_handlers = [];
  var m_metrics = {};

  function createNew(node_type, opts, callback) {
    if (!fs.existsSync(hemlock_node_directory)) {
      callback('Directory does not exist: ' + hemlock_node_directory);
      return;
    }
    if (!fs.statSync(hemlock_node_directory).isDirectory()) {
      callback('Not a directory: ' + hemlock_node_directory);
      return;
    }
    if (fs.existsSync(hemlock_node_directory + '/' + options.config_directory_name)) {
      callback(`Cannot create new ${node_type}. File or directory ${options.config_directory_name} already exists.`);
      return;
    }
    fs.mkdirSync(hemlock_node_directory + '/' + options.config_directory_name);
    set_config('node_type', node_type);
    callback(null);
  }

  function initialize(callback) {
    if (!fs.existsSync(hemlock_node_directory)) {
      callback('Directory does not exist: ' + hemlock_node_directory);
      return;
    }
    if (!fs.statSync(hemlock_node_directory).isDirectory()) {
      callback('Not a directory: ' + hemlock_node_directory);
      return;
    }

    ///////////////////////////////////////////////////////////////////////////
    if ((!get_config('node_type')) && (get_config('kbnode_type'))) {
      if (get_config('kbnode_type') == 'hub')
        set_config('node_type', 'hub');
      else if (get_config('kbnode_type') == 'share')
        set_config('node_type', 'leaf');
    }
    if ((!get_config('node_id')) && (get_config('kbnode_id'))) {
      set_config('node_id', get_config('kbnode_id'));
    }
    ///////////////////////////////////////////////////////////////////////////

    set_config('network_type', options.network_type || 'kbucket');

    m_node_id = get_config('node_id');
    m_node_type = get_config('node_type');

    if ((!m_node_id) || (!m_node_type)) {
      callback('Invalid node.');
      return;
    }

    callback(null);
  }

  function runInteractiveConfiguration(opts, callback) {
    var questions = [];
    if (!opts.clone_only) {
      questions.push({
        type: 'input',
        name: 'name',
        message: `Name for this ${options.node_type_label}:`,
        default: get_config('name') || require('path').basename(hemlock_node_directory),
        validate: is_valid_hemlock_node_name
      });
      var str;
      if (m_node_type == 'hub') {
        str = 'Are you hosting this hub for scientific research purposes (yes/no)?';
      } else if (m_node_type == 'leaf') {
        str = 'Are you sharing these resources for scientific research purposes (yes/no)?';
      } else {
        console.error('Unexpected hemlock_node type: ' + m_node_type);
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
        message: `Brief description of this ${options.node_type_label}:`,
        default: get_config('description') || '',
        validate: is_valid_description,
        optional: false
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
      let default_parent_hub_url = process.env.KBUCKET_URL || 'https://kbucket.flatironinstitute.org';
      if (get_config('network_type') == 'lari')
        default_parent_hub_url = 'https://larihub.org';
      if (m_node_type == 'leaf') {
        questions.push({
          //type: 'list',
          type: 'input',
          name: 'confirm_share',
          message: `Share all resources associated with the directory ${hemlock_node_directory}? (yes/no)`,
          //choices: ['yes', 'no'],
          default: get_config('confirm_share') || '',
        });
        questions.push({
          type: 'input',
          name: 'listen_url',
          message: `Listen url for this ${opts.node_type_label} (use . for http://localhost:[port]):`,
          default: get_config('listen_url') || '.',
          validate: is_valid_url
        });
        if (get_config('network_type') == 'lari') {
          questions.push({
            type: 'input',
            name: 'processing_passcode',
            message: 'Passcode for this lari resource:',
            default: get_config('processing_passcode') || '',
            optional: true
          });
        }
        questions.push({
          type: 'input',
          name: 'parent_hub_url',
          message: 'Parent hub url:',
          default: get_config('parent_hub_url') || default_parent_hub_url,
          validate: is_valid_url
        });
        questions.push({
          type: 'input',
          name: 'parent_hub_passcode',
          message: 'Parent hub passcode:',
          default: get_config('parent_hub_passcode') || '',
          optional: true
        });
      }
      if (m_node_type == 'hub') {
        questions.push({
          type: 'input',
          name: 'listen_port',
          message: 'Listen port for this hub:',
          default: get_config('listen_port') || (opts.default_hub_listen_port || 3240),
          validate: is_valid_port
        });
        questions.push({
          type: 'input',
          name: 'passcode',
          message: 'Passcode for this hub:',
          default: get_config('passcode') || '',
          optional: true
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
          default: get_config('parent_hub_url') || default_parent_hub_url,
          validate: is_valid_url
        });
        questions.push({
          type: 'input',
          name: 'parent_hub_passcode',
          message: 'Parent hub passcode:',
          default: get_config('parent_hub_passcode') || '',
          optional: true
        });
      }
    } else {
      //clone only
      set_config('readonly', true);
      set_config('node_type', opts.info.node_type);
      set_config('name', opts.info.name);
      set_config('description', opts.info.description);
      set_config('owner', opts.info.owner);
      set_config('owner_email', opts.info.owner_email);
    }

    for (var i in questions) {
      let qq = questions[i];
      qq.message = `[${get_config('network_type')}] ${qq.message}`;
    }

    if (opts.auto_use_defaults) {
      for (var i in questions) {
        var qq = questions[i];

        if (qq.default) {
          set_config(qq.name, qq.default);
        } else {
          if (!qq.optional) {
            console.error('Aborting due to missing required field: ' + qq.name);
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

  function is_valid_hemlock_node_name(str) {
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
      console.info('This system should only be used to share resources for scientific research purposes.');
      process.exit(-1);
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
    url=url.split('[port]').join(m_listen_port);
    return url;
  }

  function generate_pem_files_and_node_id(opts, callback) {
    if (!opts.clone_only) {
      if (get_config('node_id')) {
        callback('Cannot generate public/private keys because node id has already been set.');
        return;
      }
      var pair = keypair();
      var private_key = pair.private;
      var public_key = pair.public;
      write_text_file(m_config_dir + '/private.pem', private_key);
      write_text_file(m_config_dir + '/public.pem', public_key);
      var node_id = sha1(public_key).slice(0, 12); //important
      set_config('node_id', node_id);
    } else {
      set_config('node_id', opts.info.node_id);
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

  function getNodeInfo() {
    var ret = {
      node_id: that.hemlockNodeId(),
      node_type: that.hemlockNodeType(),
      name: that.getConfig('name'),
      description: that.getConfig('description'),
      owner: that.getConfig('owner'),
      owner_email: that.getConfig('owner_email'),
      listen_url: that.listenUrl() || undefined,
      public_key: that.publicKey() || undefined,
      cas_upload_url: that.getConfig('cas_upload_url') || undefined
    };
    return ret;
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