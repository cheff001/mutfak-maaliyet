// index.html içinden tarifleri, alerjen listesini ve eşleşmelerini JSON olarak çıkarır.
const fs=require('fs');
const h=fs.readFileSync(process.argv[2],'utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/)[1];
const i=m.indexOf('var RAW=[');const j=m.indexOf('\n];',i)+3;
const RAW=eval('('+m.slice(i+8,j-1)+')');
const a=m.indexOf('var ALGL=');const b=m.indexOf('function algOf');
const ctx={};new Function('ctx',m.slice(a,b)+';ctx.ALGL=ALGL;ctx.ALG=ALG;')(ctx);
process.stdout.write(JSON.stringify({raw:RAW,algl:ctx.ALGL,alg:ctx.ALG}));
