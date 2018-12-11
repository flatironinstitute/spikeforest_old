#!/usr/bin/env node

let PairioClient=require(__dirname+'/index.js').PairioClient;
let test_pairioclient=require(__dirname+'/index.js').test_pairioclient;

async function main() {
	await test_pairioclient();
}
main();