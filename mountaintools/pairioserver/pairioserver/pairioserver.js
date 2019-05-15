/*

Pairio

API:
GET:/get/[collection]/[key]

  Returns the JSON of the following object
  {
    success:[boolean:success],
    value:[string:value],
    error:[string:error]
  }

GET:/get/[collection]/[key]/[subkey]

  Returns the JSON of the following object
  {
    success:[boolean:success],
    value:[string:value],
    error:[string:error]
  }

GET:/set/[collection]/[key]/[value]?signature=[signature]

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

  and [token] is the secret token associated with the collection.

Similar for:
GET:/set/[collection]/[key]/[subkey]/[value]?signature=[signature]

GET:/remove/[collection]/[key]?signature=[signature]

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

  and [token] is the secret token associated with the collection.

Similar for:
GET:/remove/[collection]/[key]/[subkey]?signature=[signature]

To create a new collection on the server:

GET:/admin/create/[new_collection]/[new_collection_token]?signature=[signature]

  where [signature] is the SHA-1 hash of the JSON string associated
  with the object:

  {
      path:[path of GET request],
      token:[admin_token]
  }

  and [admin_token] is the secret admin token associated with the server.

The admin token is stored in the environment variable CAIRIO_ADMIN_TOKEN
on the server.

The mongodb url is stored in the environment variable MONGODB_URL

Information about a collection may be obtained via

GET:/admin/get/[collection]/info?signature=[signature]

  where [signature] is the SHA-1 hash of the JSON string associated
  with the object:

  {
      path:[path of GET request],
      token:[admin_token]
  }

  and [admin_token] is as above.

*/

let a = require('dotenv').config({
    path: __dirname + '/../.env'
});

const express = require('express');
const cors = require('cors');
const MongoClient = require('mongodb').MongoClient;
const crypto = require('crypto');
const fs = require('fs');

const MAX_KEY_LENGTH = 40;
//const MAX_VALUE_LENGTH=40;
const MAX_VALUE_LENGTH = 10000; // should be 80

const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://localhost:27017'

function PairioServer(API) {
    this.app = function() {
        return m_app;
    };

    let m_app = express();
    m_app.set('json spaces', 4); // when we respond with json, this is how it will be formatted
    m_app.use(cors());

    m_app.use(express.json());

    // API /get/:collection/:key
    m_app.get('/get/:collection/:key', async function(req, res) {
        await handle_get(req, res);
    });
    m_app.get('/get/:collection/:key/:subkey', async function(req, res) {
        await handle_get(req, res);
    });
    async function handle_get(req, res) {
        let params = req.params;
        if (params.key.length > MAX_KEY_LENGTH) {
            res.json({
                success: false,
                error: 'Invalid key'
            });
            return;
        }
        if ((params.subkey) && (params.subkey.length > MAX_KEY_LENGTH)) {
            res.json({
                success: false,
                error: 'Invalid subkey'
            });
            return;
        }
        try {
            obj = await API.get(params.collection, params.key, params.subkey || null);
        } catch (err) {
            console.error(err);
            res.json({
                success: false,
                error: err.message
            });
            return;
        }
        res.json(obj);
    }

    // API /set/:collection/:key/:value
    m_app.get('/set/:collection/:key/:value', async function(req, res) {
        let query = req.query;
        let params = req.params;
        if (!query.signature) {
            res.json({
                success: false,
                error: 'Missing query parameter: signature'
            });
            return;
        }
        let ok = await verify_collection_signature(params.collection, `/set/${params.collection}/${params.key}/${params.value}`, query.signature);
        if (!ok) {
            res.json({
                success: false,
                error: 'Invalid signature'
            });
            return;
        }
        await handle_set(req, res);
    });
    // API /set/:collection/:key/:subkey/:value
    m_app.get('/set/:collection/:key/:subkey/:value', async function(req, res) {
        let query = req.query;
        let params = req.params;
        if (!query.signature) {
            res.json({
                success: false,
                error: 'Missing query parameter: signature'
            });
            return;
        }
        let ok = await verify_collection_signature(params.collection, `/set/${params.collection}/${params.key}/${params.subkey}/${params.value}`, query.signature);
        if (!ok) {
            res.json({
                success: false,
                error: 'Invalid signature'
            });
            return;
        }
        await handle_set(req, res);
    });
    // API /remove/:collection/:key
    m_app.get('/remove/:collection/:key', async function(req, res) {
        let query = req.query;
        let params = req.params;
        if (!query.signature) {
            res.json({
                success: false,
                error: 'Missing query parameter: signature'
            });
            return;
        }
        let ok = await verify_collection_signature(params.collection, `/remove/${params.collection}/${params.key}`, query.signature);
        if (!ok) {
            res.json({
                success: false,
                error: 'Invalid signature'
            });
            return;
        }
        await handle_set(req, res);
    });
    // API /remove/:collection/:key/:subkey
    m_app.get('/remove/:collection/:key/:subkey', async function(req, res) {
        let query = req.query;
        let params = req.params;
        if (!query.signature) {
            res.json({
                success: false,
                error: 'Missing query parameter: signature'
            });
            return;
        }
        let ok = await verify_collection_signature(params.collection, `/remove/${params.collection}/${params.key}/${params.subkey}`, query.signature);
        if (!ok) {
            res.json({
                success: false,
                error: 'Invalid signature'
            });
            return;
        }
        await handle_set(req, res);
    });

    async function handle_set(req, res) {
        let query = req.query;
        let params = req.params;
        if (params.value) params.value = atob(params.value);
        if (params.key.length > MAX_KEY_LENGTH) {
            res.json({
                success: false,
                error: 'Invalid key'
            });
            return;
        }
        if ((params.subkey) && (params.subkey.length > MAX_KEY_LENGTH)) {
            res.json({
                success: false,
                error: 'Invalid subkey'
            });
            return;
        }
        if ((params.value) && (params.value.length > MAX_VALUE_LENGTH)) {
            res.json({
                success: false,
                error: 'Length of value is too long'
            });
            return;
        }

        let overwrite = true;
        if (query.overwrite == 'false')
            overwrite = false;
        try {
            obj = await API.set(params.collection, params.key, params.subkey, params.value, overwrite);
        } catch (err) {
            console.error(err);
            res.json({
                success: false,
                error: err.message
            });
            return;
        }
        res.json(obj);
    }

    // API /admin/create/:collection/:collectiontoken
    m_app.get('/admin/create/:collection/:collectiontoken', async function(req, res) {
        let params = req.params;
        let query = req.query;
        if (!query.signature) {
            res.json({
                success: false,
                error: 'Missing query parameter: signature'
            });
            return;
        }
        let ok = await verify_admin_signature(`/admin/create/${params.collection}/${params.collectiontoken}`, query.signature);
        if (!ok) {
            res.json({
                success: false,
                error: 'Invalid signature'
            });
            return;
        }
        try {
            obj = await API.adminCreateCollection(params.collection, params.collectiontoken);
        } catch (err) {
            console.error(err);
            res.json({
                success: false,
                error: err.message
            });
            return;
        }
        res.json(obj);
    });

    // API /admin/get/:collection/info
    m_app.get('/admin/get/:collection/info', async function(req, res) {
        let params = req.params;
        let query = req.query;
        if (!query.signature) {
            res.json({
                success: false,
                error: 'Missing query parameter: signature'
            });
            return;
        }
        let ok = await verify_admin_signature(`/admin/get/${params.collection}/params`, query.signature);
        if (!ok) {
            res.json({
                success: false,
                error: 'Invalid signature'
            });
            return;
        }
        try {
            obj = await API.adminGetCollectionInfo(params.collection);
        } catch (err) {
            console.error(err);
            res.json({
                success: false,
                error: err.message
            });
            return;
        }
        res.json(obj);
    });

    function sha1_of_object(obj) {
        let shasum = crypto.createHash('sha1');
        shasum.update(JSON.stringify(obj));
        return shasum.digest('hex');
    }
    async function verify_collection_signature(collection, path, signature) {
        let info = await API.DB.getCollectionInfo(collection);
        if (!info) return false;
        if (!info.token) return false;
        let sig = sha1_of_object({
            path: path,
            token: info.token
        });
        return (signature == sig);
    }
    async function verify_admin_signature(path, signature) {
        let admin_token = process.env.CAIRIO_ADMIN_TOKEN;
        if (!admin_token) {
            console.warn('Warning: CAIRIO_ADMIN_TOKEN not set');
            return false;
        }
        let sig = sha1_of_object({
            path: path,
            token: admin_token
        });
        return (signature == sig);
    }
}

function PairioApi(DB) {
    let that = this;
    this.DB = DB;
    this.get = async function(collection, key, subkey) {
        let doc = await DB.getCollectionPair(collection, key, subkey);
        if (!doc) {
            return {
                success: false,
                error: 'Pair not found.'
            };
        }
        let value = doc.value || null;
        if (!value) {
            return {
                success: false,
                error: 'Unexpected: value is null or empty in document: ' + value
            };
        }
        return {
            success: true,
            value: value
        }
    };

    this.set = async function(collection, key, subkey, value, overwrite) {
        try {
            await DB.setCollectionPair(collection, key, subkey, value, overwrite);
        } catch (err) {
            return {
                success: false,
                error: 'Error setting collection pair: ' + err.message
            };
        }
        return {
            success: true
        }
    };

    this.adminCreateCollection = async function(collection, collectiontoken) {
        let info = await DB.getCollectionInfo(collection);
        if (!info) info = {};
        //info.token=await create_random_token(12);
        info.token = collectiontoken;
        await DB.setCollectionInfo(collection, info);
        return {
            success: true,
            token: info.token
        };
    };

    this.adminSetCollectionParam = async function(collection, key, value) {
        let info = await DB.getCollectionInfo(collection);
        info = info || {};
        info.params = info.params || {};
        info.params[key] = value;
        await DB.setCollectionInfo(collection, info);
        return {
            success: true
        };
    };

    this.adminGetCollectionInfo = async function(collection) {
        let info = await DB.getCollectionInfo(collection);
        if (!info) info = {};
        info.params = info.params || {};
        return {
            success: true,
            params: info.params
        };
    };

    async function create_random_token(num_chars) {
        return new Promise(function(resolve, reject) {
            crypto.randomBytes(num_chars / 2, function(ex, buf) {
                let token = buf.toString('hex')
                resolve(token);
            });
        });
    }
}

function PairioDB() {
    let m_db = null;
    this.connect = async function(url, db_name) {
        let client = await MongoClient.connect(url, {
            useNewUrlParser: true
        });
        m_db = client.db(db_name);
    }
    this.getCollectionPair = async function(collection, key, subkey) {
        if (!m_db) {
            throw new Error('Not connected to database');
        }
        let record;
        if (subkey) {
            if (subkey == '-') {
                record = {
                    collection: collection,
                    key: key,
                    subkey: { $exists: true }
                }
            } else {
                record = {
                    collection: collection,
                    key: key,
                    subkey: subkey
                }
            }
        } else {
            record = {
                collection: collection,
                key: key,
                subkey: { $exists: false }
            }
        }
        let collec = m_db.collection("collectionpairs");
        let cursor = collec.find(record);
        let docs = await cursor.toArray();
        if (subkey == '-') {
            let val00 = {};
            for (let ii = 0; ii < docs.length; ii++) {
                val00[docs[ii].subkey] = docs[ii].value;
            }
            return { collection: collection, key: key, subkey: subkey, value: JSON.stringify(val00) };
        }
        if (docs.length > 1) {

            console.warn('Warning: unexpected: more than one document found in getCollectionPair');
        }
        if (docs.length != 1) return null;
        return docs[0];
    };
    this.setCollectionPair = async function(collection, key, subkey, value, overwrite) {
        if (!m_db) {
            throw new Error('Not connected to database');
        }
        let record;
        if (subkey) {
            if (subkey == '-') {
                if (value) {
                    throw new Error('Cannot set value with subkey of "-"');
                }
                record = {
                    collection: collection,
                    key: key,
                    subkey: { $exists: true }
                }
            } else {
                record = {
                    collection: collection,
                    key: key,
                    subkey: subkey
                }
            }
        } else {
            record = {
                collection: collection,
                key: key
            }
        }

        let collec = m_db.collection("collectionpairs");
        if (!value) {
            //await collec.remove({collection:collection,key:key});
            if (subkey == '-') {
                await collec.deleteMany(record);
            } else {
                await collec.deleteOne(record);
            }
        } else if (overwrite) {
            await collec.updateOne(record, {
                $set: {
                    value: value
                }
            }, {
                upsert: true
            });
        } else {
            let tmp = await collec.updateOne(record, {
                $setOnInsert: {
                    value: value
                }
            }, {
                upsert: true
            });
            if (tmp.matchedCount > 0) {
                throw new Error('Key exists -- cannot overwrite.');
            }
        }
    };
    this.getCollectionInfo = async function(collection) {
        if (!m_db) {
            throw new Error('Not connected to database');
        }
        let collec = m_db.collection("collectioninfo");
        let cursor = collec.find({
            collection: collection
        });
        let docs = await cursor.toArray();
        if (docs.length > 1) {
            console.warn('Warning: unexpected: more than one document found in getCollectionInfo');
        }
        if (docs.length != 1) return null;
        return docs[0].info || {};
    };
    this.setCollectionInfo = async function(collection, info) {
        if (!m_db) {
            throw new Error('Not connected to database');
        }
        let collec = m_db.collection("collectioninfo");
        collec.updateOne({
            collection: collection
        }, {
            $set: {
                info: info
            }
        }, {
            upsert: true
        });
    };
}

function atob(x) {
    return Buffer.from(x, 'base64').toString();
}


async function main() {
    let admin_token = process.env.CAIRIO_ADMIN_TOKEN;
    if (!admin_token) {
        console.warn('ERROR: You must set the CAIRIO_ADMIN_TOKEN environment variable.');
        process.exit(-1);
    }

    let DB = new PairioDB();
    try {
        await DB.connect(MONGODB_URL, 'cairio');
    } catch (err) {
        console.error(err);
        console.error('Error connecting to database: ' + err.message);
        process.exit(-1);
    }
    let API = new PairioApi(DB);
    let SERVER = new PairioServer(API);
    try {
        await start_http_server(SERVER.app());
    } catch (err) {
        console.error(err);
        console.error('Error starting server: ' + err.message);
        process.exit(-1);
    }
}
try {
    main();
} catch (err) {
    console.error(err);
}

async function start_http_server(app) {
    let listen_port = process.env.CAIRIO_PORT || process.env.PORT || 25340;
    app.port = listen_port;
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