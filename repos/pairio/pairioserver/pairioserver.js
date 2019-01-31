/*

Pairio is a service for sharing key/value pairs per user
where both the keys and values are no longer than 40 characters *see exception below*.
This is useful for associating the hash of an input with the
hash of an output.

Exception: we now allow values to be longer than 40 characters
for a relatively small number of records. This is to enable
storing of configuration records. (Need to think about this)

API:
GET:/get/[user]/[key]

  Returns the JSON of the following object
  {
    success:[boolean:success],
    value:[string:value],
    error:[string:error]
  }

GET:/set/[user]/[key]/[value]?signature=[signature]

  Returns the JSON of the following object
  {
    success:[boolean:success],
    error:[string:error]
  }

  where [signature] is the SHA-1 hash of the JSON string associated
  with the object:

  {
      path:[path of GET request],
      token:[token]
  }

  and [token] is the secret token associated with the user.

GET:/remove/[user]/[key]?signature=[signature]

  Returns the JSON of the following object
  {
    success:[boolean:success],
    error:[string:error]
  }

  where [signature] is the SHA-1 hash of the JSON string associated
  with the object:

  {
      path:[path of GET request],
      token:[token]
  }

  and [token] is the secret token associated with the user.

To create an account on the server:

GET:/admin/register/[new_user]/[new_user_token]?signature=[signature]

  where [signature] is the SHA-1 hash of the JSON string associated
  with the object:

  {
      path:[path of GET request],
      token:[admin_token]
  }

  and [admin_token] is the secret admin token associated with the server.

The admin token is stored in the environment variable PAIRIO_ADMIN_TOKEN
on the server.

The quota for a user may be set via

GET:/admin/set/[user]/max_num_pairs/[max_num_pairs]?signature=[signature]

  where [max_num_pairs] is the maximum number of pairs that may be set for [user]
  and [signature] is the SHA-1 hash of the JSON string associated
  with the object:

  {
      path:[path of GET request],
      token:[admin_token]
  }

  and [admin_token] is as above.

GET:/admin/set/[user]/max_num_long_pairs/[max_num_long_pairs]?signature=[signature]

  similar as above

Information about a user may be obtained via

GET:/admin/get/[user]/params?signature=[signature]

  where [signature] is the SHA-1 hash of the JSON string associated
  with the object:

  {
      path:[path of GET request],
      token:[admin_token]
  }

  and [admin_token] is as above.

*/

require('dotenv').config({ path: __dirname+'/../.env' });

const express = require('express');
const cors = require('cors');
const MongoClient = require('mongodb').MongoClient;
const crypto = require('crypto');
const fs = require('fs');

const default_max_num_pairs=10000;
const default_max_num_long_pairs=100;
const MAX_KEY_LENGTH=40;
//const MAX_VALUE_LENGTH=40;
const MAX_VALUE_LENGTH=10000;

function PairioServer(API) {
  this.app = function() {
    return m_app;
  };

  let m_app = express();
  m_app.set('json spaces', 4); // when we respond with json, this is how it will be formatted
  m_app.use(cors());

  m_app.use(express.json());

  // API /get/:user/:key
  m_app.get('/get/:user/:key', async function(req, res) {
    let params = req.params;
    if (params.key.length>MAX_KEY_LENGTH) {
      res.json({
        success:false,
        error:'Invalid key'
      });
    }
    try {
      obj = await API.get(params.user,params.key);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });

  // API /set/:user/:key/:value
  m_app.get('/set/:user/:key/:value', async function(req, res) {
    let params = req.params;
    if (params.key.length>MAX_KEY_LENGTH) {
      res.json({
        success:false,
        error:'Invalid key'
      });
      return;
    }
    if (params.value.length>MAX_VALUE_LENGTH) {
      res.json({
        success:false,
        error:'Length of value is too long'
      });
      return;
    }
    let query = req.query;
    if (!query.signature) {
      res.json({
        success:false,
        error:'Missing query parameter: signature'
      });
      return;
    }
    let ok=await verify_user_signature(params.user,`/set/${params.user}/${params.key}/${params.value}`,query.signature);
    if (!ok) {
      res.json({
        success:false,
        error:'Invalid signature'
      });
      return;
    }
    
    let is_long_pair=(params.value.length>40);
    if (!is_long_pair) {
      let test=await API.get(params.user,params.key);
      if (!test.success) {
        ok=await increment_user_num_pairs(params.user);
        if (!ok) {
          res.json({
            success:false,
            error:'Unable to increment user pair count. Quota exceeded?'
          });
          return;
        }
      }  
    }
    else {
      let test=await API.get(params.user,params.key);
      if ( (!test.success) || (test.value.length<=40) ) {
        ok=await increment_user_num_long_pairs(params.user);
        if (!ok) {
          res.json({
            success:false,
            error:'Unable to increment user *long* pair count. Quota exceeded?'
          });
          return;
        }
      }  
    }
    
    let overwrite=true;
    if (query.overwrite=='false')
      overwrite=false;
    try {
      obj = await API.set(params.user,params.key,params.value,overwrite);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });

  // API /remove/:user/:key
  m_app.get('/remove/:user/:key', async function(req, res) {
    let params = req.params;
    if (params.key.length>MAX_KEY_LENGTH) {
      res.json({
        success:false,
        error:'Invalid key'
      });
    }
    let query = req.query;
    if (!query.signature) {
      res.json({
        success:false,
        error:'Missing query parameter: signature'
      });
      return;
    }
    let ok=await verify_user_signature(params.user,`/remove/${params.user}/${params.key}`,query.signature);
    if (!ok) {
      res.json({
        success:false,
        error:'Invalid signature'
      });
      return;
    }
    let test=await API.get(params.user,params.key);
    try {
      obj = await API.set(params.user,params.key,null,true);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });

  // API /admin/register/:user/:usertoken
  m_app.get('/admin/register/:user/:usertoken', async function(req, res) {
    let params = req.params;
    let query = req.query;
    if (!query.signature) {
      res.json({
        success:false,
        error:'Missing query parameter: signature'
      });
      return;
    }
    let ok=await verify_admin_signature(`/admin/register/${params.user}/${params.usertoken}`,query.signature);
    if (!ok) {
      res.json({
        success:false,
        error:'Invalid signature'
      });
      return;
    }
    try {
      obj = await API.adminRegister(params.user,params.usertoken);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });

  // API /admin/set/:user/max_num_pairs
  m_app.get('/admin/set/:user/max_num_pairs/:max_num_pairs', async function(req, res) {
    let params = req.params;
    let query = req.query;
    if (!query.signature) {
      res.json({
        success:false,
        error:'Missing query parameter: signature'
      });
      return;
    }
    let ok=await verify_admin_signature(`/admin/set/${params.user}/max_num_pairs/${params.max_num_pairs}`,query.signature);
    if (!ok) {
      res.json({
        success:false,
        error:'Invalid signature'
      });
      return;
    }
    try {
      obj = await API.adminSetUserParam(params.user,'max_num_pairs',params.max_num_pairs);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });

  // API /admin/set/:user/max_num_long_pairs
  m_app.get('/admin/set/:user/max_num_long_pairs/:max_num_long_pairs', async function(req, res) {
    let params = req.params;
    let query = req.query;
    if (!query.signature) {
      res.json({
        success:false,
        error:'Missing query parameter: signature'
      });
      return;
    }
    let ok=await verify_admin_signature(`/admin/set/${params.user}/max_num_long_pairs/${params.max_num_long_pairs}`,query.signature);
    if (!ok) {
      res.json({
        success:false,
        error:'Invalid signature'
      });
      return;
    }
    try {
      obj = await API.adminSetUserParam(params.user,'max_num_long_pairs',params.max_num_long_pairs);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });

  // API /admin/get/:user/params
  m_app.get('/admin/get/:user/params', async function(req, res) {
    let params = req.params;
    let query = req.query;
    if (!query.signature) {
      res.json({
        success:false,
        error:'Missing query parameter: signature'
      });
      return;
    }
    let ok=await verify_admin_signature(`/admin/get/${params.user}/params`,query.signature);
    if (!ok) {
      res.json({
        success:false,
        error:'Invalid signature'
      });
      return;
    }
    try {
      obj = await API.adminGetUserParams(params.user);
    }
    catch(err) {
      console.error(err);
      res.json({
        success:false,
        error:err.message
      });
      return;
    }
    res.json(obj);
  });

  async function increment_user_num_pairs(user) {
    let info=await API.DB.getUserInfo(user);
    if (!info) return false;
    info.params=info.params||{};
    info.params.num_pairs=info.params.num_pairs||0;
    let max0=info.params.max_num_pairs||default_max_num_pairs;
    if (info.params.num_pairs+1>max0) {
      return false;
    }
    info.params.num_pairs++;
    await API.DB.setUserInfo(user,info);
    return true;
  }

  async function increment_user_num_long_pairs(user) {
    let info=await API.DB.getUserInfo(user);
    if (!info) return false;
    info.params=info.params||{};
    info.params.num_long_pairs=info.params.num_long_pairs||0;
    let max0=info.params.max_num_long_pairs||default_max_num_long_pairs;
    if (info.params.num_long_pairs+1>max0) {
      return false;
    }
    info.params.num_long_pairs++;
    await API.DB.setUserInfo(user,info);
    return true;
  }

  function sha1_of_object(obj) {
    let shasum = crypto.createHash('sha1');
    shasum.update(JSON.stringify(obj));
    return shasum.digest('hex');
  }
  async function verify_user_signature(user,path,signature) {
    let info=await API.DB.getUserInfo(user);
    if (!info) return false;
    if (!info.token) return false;
    let sig=sha1_of_object({path:path,token:info.token});
    return (signature==sig);
  }
  async function verify_admin_signature(path,signature) {
    let admin_token=process.env.PAIRIO_ADMIN_TOKEN;
    if (!admin_token) {
      console.warn('Warning: PAIRIO_ADMIN_TOKEN not set');
      return false;
    }
    let sig=sha1_of_object({path:path,token:admin_token});
    return (signature==sig);
  }
}

function PairioApi(DB) {
  this.DB=DB;
  this.get=async function(user,key) {
    let doc=await DB.getUserPair(user,key);
    if (!doc) {
      return {
        success:false,
        error:'Pair not found.'
      };
    }
    let value=doc.value||null;
    if (!value) {
      return {
        success:false,
        error:'Unexpected: value is null or empty in document: '+value
      };  
    }
    return {
      success:true,
      value:value
    };
  };

  this.set=async function(user,key,value,overwrite) {
    await DB.setUserPair(user,key,value,overwrite);
    return {success:true};
  };

  this.adminRegister=async function(user,usertoken) {
    let info=await DB.getUserInfo(user);
    if (!info) info={};
    //info.token=await create_random_token(12);
    info.token=usertoken;
    await DB.setUserInfo(user,info);
    return {success:true,token:info.token};
  };

  this.adminSetUserParam=async function(user,key,value) {
    let info=await DB.getUserInfo(user);
    info=info||{};
    info.params=info.params||{};
    info.params[key]=value;
    await DB.setUserInfo(user,info);
    return {success:true};
  };

  this.adminGetUserParams=async function(user) {
    let info=await DB.getUserInfo(user);
    if (!info) info={};
    info.params=info.params||{};
    return {
      success:true,
      params:info.params
    };
  };

  async function create_random_token(num_chars) {
    return new Promise(function(resolve, reject) {
      crypto.randomBytes(num_chars/2, function(ex, buf) { 
        let token=buf.toString('hex')
        resolve(token);
      });  
    });
  }
}

function PairioDB() {
  let m_db=null;
  this.connect=async function(url,db_name) {
    let client=await MongoClient.connect(url,{ useNewUrlParser: true });
    m_db=client.db(db_name);
  }
  this.getUserPair=async function(user,key) {
    if (!m_db) {
      throw new Error('Not connected to database');
    }
    let collection=m_db.collection("userpairs");
    let cursor=collection.find({user:user,key:key});
    let docs=await cursor.toArray();
    if (docs.length>1) {
      console.warn('Warning: unexpected: more than one document found in getUserPair');
    }
    if (docs.length!=1) return null;
    return docs[0];
  }
  this.setUserPair=async function(user,key,value,overwrite) {
    if (!m_db) {
      throw new Error('Not connected to database');
    }
    let collection=m_db.collection("userpairs");
    if (!value) {
      //await collection.remove({user:user,key:key});
      await collection.deleteOne({user:user,key:key});
    }
    else if (overwrite) {
      await collection.updateOne({user:user,key:key},{$set:{value: value}},{upsert:true});
    }
    else {
      let tmp=await collection.updateOne({user:user,key:key},{$setOnInsert:{value: value}},{upsert:true});  
      if (tmp.matchedCount>0) {
        throw new Error('Key exists -- cannot overwrite.');
      }
    }
  }
  this.getUserInfo=async function(user) {
    if (!m_db) {
      throw new Error('Not connected to database');
    }
    let collection=m_db.collection("userinfo");
    let cursor=collection.find({user:user});
    let docs=await cursor.toArray();
    if (docs.length>1) {
      console.warn('Warning: unexpected: more than one document found in getUserInfo');
    }
    if (docs.length!=1) return null;
    return docs[0].info||{};
  }
  this.setUserInfo=async function(user,info) {
    if (!m_db) {
      throw new Error('Not connected to database');
    }
    let collection=m_db.collection("userinfo");
    collection.updateOne({user:user},{$set:{info: info}},{upsert:true});
  }
}


async function main() {
  let DB=new PairioDB();
  try {
    await DB.connect('mongodb://localhost:27017','pairio');
  }
  catch(err) {
    console.error(err);
    console.error('Error connecting to database: '+err.message);
    process.exit(-1);
  }
  let API=new PairioApi(DB);
  let SERVER=new PairioServer(API);
  try {
    await start_http_server(SERVER.app());
  }
  catch(err) {
    console.error(err);
    console.error('Error starting server: '+err.message);
    process.exit(-1);
  }
}
main();

async function start_http_server(app) {
  let listen_port=process.env.PORT||25340;
  app.port=listen_port;
  if (process.env.SSL != null ? process.env.SSL : listen_port % 1000 == 443) {
    // The port number ends with 443, so we are using https
    app.USING_HTTPS = true;
    app.protocol = 'https';
    // Look for the credentials inside the encryption directory
    // You can generate these for free using the tools of letsencrypt.org
    const options = {
      key: fs.readFileSync(__dirname + '/encryption/privkey.pem'),
      cert: fs.readFileSync(__dirname + '/encryption/fullchain.pem'),
      ca: fs.readFileSync(__dirname + '/encryption/chain.pem')
    };

    // Create the https server
    app.server = require('https').createServer(options, app);
  } else {
    app.protocol = 'http';
    // Create the http server and start listening
    app.server = require('http').createServer(app);
  }
  await app.server.listen(listen_port);
  console.info(`Server is running ${app.protocol} on port ${app.port}`);
}
