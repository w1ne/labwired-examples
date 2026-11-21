#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
const [source,out] = process.argv.slice(2);
const {parseSExpr}=await import(pathToFileURL(path.join(process.env.LABWIRED_ROOT,'packages/board-config/src/import/sexpr.ts')));
const text=fs.readFileSync(source,'utf8'), parsed=parseSExpr(text);
if(!parsed.ok)throw new Error(parsed.message);
const root=parsed.value[0],forms=(n,h)=>n.filter(x=>Array.isArray(x)&&x[0]===h),form=(n,h)=>forms(n,h)[0];
const rootUuid=form(root,'uuid')[1],references={};
for(const symbol of forms(root,'symbol')){
 const ref=forms(symbol,'property').find(p=>p[1]==='Reference')?.[2];
 if(!ref||ref.startsWith('#'))continue;
 const unit=Number(form(symbol,'unit')[1]),uuid=form(symbol,'uuid')[1];
 const record=references[ref]??{instances:[]};
 record.instances.push({unit,uuid});
 if(unit===1){if(record.unit1Uuid)throw new Error('Duplicate unit1 '+ref);record.unit1Uuid=uuid;record.path='/'+rootUuid+'/'+uuid;}
 references[ref]=record;
}
for(const [ref,r]of Object.entries(references))if(!r.unit1Uuid)throw new Error('Missing unit1 '+ref);
fs.writeFileSync(out,JSON.stringify({sourceSha256:createHash('sha256').update(text).digest('hex'),rootUuid,references},null,2)+'\n');
