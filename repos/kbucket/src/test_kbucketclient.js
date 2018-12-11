#!/usr/bin/env node

const KBucketClient=require(__dirname+'/index.js').KBucketClient;

async function main() {
	let client=new KBucketClient();
	client.setConfig({share_ids:['magland.kbshare1']});
	let url=await client.findFile('sha1://ed9d81ba1b2e69ffe6efbb21d220fb21de1ab667/params.json');
	console.log(url);
}
main();