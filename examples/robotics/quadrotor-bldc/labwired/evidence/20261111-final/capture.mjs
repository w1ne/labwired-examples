import { chromium } from '/data/worktrees/labwired-quad-runtime-20261111/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
const dir='/tmp/quad-runtime-final'; await fs.mkdir(dir,{recursive:true});
const actual=JSON.parse(await fs.readFile('/tmp/quad-runtime-project-public.json','utf8'));
const mappings=JSON.parse(await fs.readFile('/home/andrii/scratch/labwired-quad-mechanical-20261111/examples/robotics/quadrotor-bldc/cad/runtime-bindings.json','utf8'));
const diagram=JSON.parse(actual.project.diagram_json);
diagram.mechanical={provider:'kernelcad',slug:'DyJ405zg',version:3,title:'Quadrotor propulsion',electronics:{version:1,...mappings}};
actual.project.diagram_json=JSON.stringify(diagram);
await fs.writeFile(dir+'/local-project-fixture.json',JSON.stringify(actual,null,2));
const sourceTrees=['/data/worktrees/labwired-motor-cad-bridge-20261111','/data/worktrees/kernelcad-motor-runtime-20261111'];
const provenance=sourceTrees.map(cwd=>({path:cwd,head:execFileSync('git',['rev-parse','HEAD'],{cwd,encoding:'utf8'}).trim(),dirty:execFileSync('git',['status','--short','--ignore-submodules=all'],{cwd,encoding:'utf8'}).trim()}));
await fs.writeFile(dir+'/provenance.json',JSON.stringify({sourceTrees:provenance,scriptSha256:crypto.createHash('sha256').update(await fs.readFile(process.argv[1])).digest('hex'),localDevelopmentAuthDisabled:true,compiler:'https://api.labwired.com/v1/compile',receiverBrowserOrigin:'https://app.kernelcad.com',receiverAssetOrigin:'http://127.0.0.1:4331',savedProjectId:'7c92d38a4f2ac205aa91502291fde0d8',cadRevision:3},null,2));
const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--enable-webgl','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
const ctx=await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1,recordVideo:{dir,size:{width:1280,height:720}}});
await ctx.addInitScript(()=>{
 window.__quadFrames=[];window.__quadWorkers=[];
 window.addEventListener('message',e=>{if(e.data?.type?.startsWith('kernelcad.runtime.'))window.__quadFrames.push({epochMs:Date.now(),time:performance.now(),origin:e.origin,data:e.data});});
 const NativeWorker=window.Worker;let serial=0;
 window.Worker=class EvidenceWorker extends NativeWorker{
  constructor(...args){super(...args);const id=++serial;const url=String(args[0]);const record=(direction,data)=>{
   if(!data||typeof data!=='object'||!['lab','labFrame','labSnapshot','snapshot','command','ready','init','initError','stepError','commandError'].includes(data.t))return;
   let value=data;
   const state=s=>({pc:s.pc,cycles:s.cycles,boardIoStates:s.boardIoStates,actuatorStates:s.actuatorStates,boardIoConfig:s.boardIoConfig,analogStates:s.analogStates,peripheralSnapshots:s.peripheralSnapshots,uartOutput:s.uartOutput,debug:s.debug});
   if(data.t==='labSnapshot')value={t:data.t,states:data.states.map(x=>({chip:x.chip,state:state(x.state)}))};
   else if(data.t==='snapshot')value={...data,state:state(data.state)};
   else if(data.t==='lab'&&data.msg?.t==='snapshot')value={...data,msg:{...data.msg,state:state(data.msg.state)}};
   else if(data.t==='init'||(data.t==='lab'&&data.msg?.t==='init')){const m=data.msg??data;const p=m.payload??{};const clean={...m,payload:{mode:p.mode,labNodeId:p.labNodeId,labWorld:p.labWorld,systemYaml:p.systemYaml,chipYaml:p.chipYaml,firmwareLength:p.firmware?.length,runtimeSnapshotLength:p.runtimeSnapshot?.length}};value=data.msg?{...data,msg:clean}:clean;}
   window.__quadWorkers.push({epochMs:Date.now(),time:performance.now(),worker:id,url,direction,data:structuredClone(value)});
  };this.addEventListener('message',e=>record('received',e.data));const send=this.postMessage;this.postMessage=function(...a){record('sent',a[0]);return send.apply(this,a);};}
 };
});
await ctx.route('https://api.labwired.com/v1/projects/7c92d38a4f2ac205aa91502291fde0d8',route=>route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(actual)}));
await ctx.route('https://app.kernelcad.com/**',async route=>{try{const u=new URL(route.request().url());if(u.pathname.startsWith('/api/'))return route.continue();const response=await ctx.request.get('http://127.0.0.1:4331'+u.pathname+u.search,{timeout:60000});if(response.headers()['content-type']?.includes('text/html')&&!u.pathname.startsWith('/embed/')&&!u.pathname.startsWith('/p/'))return route.continue();await route.fulfill({response});}catch(e){console.log('ROUTE_FAIL',route.request().url().split('?')[0],e.message.split('\n')[0]);}});
const page=await ctx.newPage();let cadFrame;const started=Date.now();const events=[];const compiles=[];const pending=[];
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
async function mark(name,extra={}){const e={name,epochMs:Date.now(),elapsedMs:Date.now()-started,...extra};events.push(e);console.log('MARK',JSON.stringify(e));await fs.writeFile(dir+'/events.json',JSON.stringify(events,null,2));}
async function checkpoint(name){await fs.writeFile(dir+'/worker-'+name+'.json',JSON.stringify(await page.evaluate(()=>window.__quadWorkers??[]),null,2));if(cadFrame)await fs.writeFile(dir+'/cad-'+name+'.json',JSON.stringify(await cadFrame.evaluate(()=>window.__quadFrames??[]).catch(()=>[]),null,2));await fs.writeFile(dir+'/body-'+name+'.txt',await page.locator('body').innerText());if(cadFrame)await fs.writeFile(dir+'/ui-'+name+'.json',JSON.stringify(await cadFrame.evaluate(()=>({status:document.querySelector('[data-testid="electronics-runtime-status"]')?.dataset,rows:[...document.querySelectorAll('[data-testid="runtime-motor-row"]')].map(x=>({...x.dataset,text:x.textContent}))})),null,2));}
page.on('pageerror',e=>console.log('PAGE_ERROR',e.message));
page.on('console',m=>{if(m.type()==='error')console.log('CONSOLE_ERROR',m.text().slice(0,200));});
page.on('response',r=>{if(r.url().includes('api.labwired.com/v1/compile'))pending.push((async()=>{const request=r.request().postDataJSON();const body=await r.text();const item={epochMs:Date.now(),status:r.status(),request,requestSha256:sha(JSON.stringify(request)),responseSha256:sha(body),response:JSON.parse(body)};compiles.push(item);await fs.writeFile(dir+'/compiles.json',JSON.stringify(compiles,null,2));console.log('COMPILE',r.status(),item.requestSha256,Object.keys(request));})().catch(e=>console.log('COMPILE_CAPTURE_FAIL',e.message)));});
try{
 await mark('navigate',{scope:'Local patched LabWired sender and KernelCAD frontend; real saved C sources, real hosted compiler, existing WASM motor plants; 24 V reduced-order propulsion bench'});
 await page.goto('http://127.0.0.1:4330/p/7c92d38a4f2ac205aa91502291fde0d8/edit?run=1',{waitUntil:'domcontentloaded',timeout:90000});
 await page.getByTestId('hardware-view-kernelcad').waitFor({state:'visible',timeout:90000});
 await page.getByTestId('hardware-view-kernelcad').click();
 for(let n=0;n<120&&!cadFrame;n++){cadFrame=page.frames().find(f=>f.url().includes('app.kernelcad.com/embed/'));if(!cadFrame)await page.waitForTimeout(500);}
 if(!cadFrame)throw Error('No KernelCAD frame');
 await cadFrame.waitForFunction(()=>{const rows=[...document.querySelectorAll('[data-testid="runtime-motor-row"]')];return rows.length===4&&rows.every(x=>Math.abs(Number(x.dataset.speedRpm))>200&&x.dataset.controlState==='inverter');},{},{timeout:90000});
 await page.mouse.move(855,350);await page.mouse.wheel(0,-260);await page.waitForTimeout(1500);
 await mark('healthy-four-motors');await checkpoint('healthy');await page.waitForTimeout(10000);
 await page.getByTestId('hardware-view-circuit').click();await page.waitForTimeout(1500);
 const fault=page.locator('g[data-part-id="fault1"]');await fault.waitFor({state:'visible',timeout:15000});
 console.log('FAULT_ELEMENT',await fault.evaluate(el=>({label:el.getAttribute('aria-label'),role:el.getAttribute('role'),tabIndex:el.getAttribute('tabindex'),bounds:el.getBoundingClientRect().toJSON()})));
 await checkpoint('before-fault');
 await fault.focus();await page.keyboard.down('Space');await mark('fault1-pressed',{action:'Focus real fault1 canvas button then Space key down; mapped active-HIGH GPIO PB7 on ctrl1'});
 await page.waitForTimeout(15000);await checkpoint('fault-held');await page.keyboard.up('Space');await mark('fault1-released');
 await page.getByTestId('hardware-view-kernelcad').click();
 await cadFrame.waitForFunction(()=>{const r=document.querySelector('[data-motion-id="M1"]');return r&&r.dataset.controlState!=='inverter';},{},{timeout:45000});
 await mark('fault-observed');await checkpoint('fault-observed');await page.waitForTimeout(10000);await checkpoint('fault-settled');
 const rows=await cadFrame.locator('[data-testid="runtime-motor-row"]').evaluateAll(els=>els.map(e=>({...e.dataset,text:e.textContent})));
 console.log('FINAL_MOTORS',JSON.stringify(rows));
 if(rows.length!==4||rows[0].controlState==='inverter'||rows.slice(1).some(x=>x.controlState!=='inverter'||Math.abs(Number(x.speedRpm))<200))throw Error('Selected fault/peer motor assertion failed');
 await page.getByRole('button',{name:'Pause system',exact:true}).click();await mark('pause-click');
 await cadFrame.waitForFunction(()=>document.querySelector('[data-testid="electronics-runtime-status"]')?.dataset.state==='paused',{},{timeout:15000});
 const readRows=()=>cadFrame.locator('[data-testid="runtime-motor-row"]').evaluateAll(els=>els.map(e=>({...e.dataset,text:e.textContent})));
 const paused=await readRows();await checkpoint('paused');await page.waitForTimeout(5000);const held=await readRows();
 if(paused.length!==4||held.some((x,i)=>x.positionRad!==paused[i].positionRad||x.sampleCurrent!=='false'))throw Error('Pause must hold exact observed pose and mark samples stale');
 await mark('pause-hold-verified',{positionsRad:held.map(x=>x.positionRad),durationMs:5000});await checkpoint('pause-held');
 await page.getByRole('button',{name:'Reset system',exact:true}).click();await mark('reset-click');
 await cadFrame.waitForFunction(()=>document.querySelector('[data-testid="electronics-runtime-status"]')?.dataset.state==='stopped',{},{timeout:15000});
 const stopped=await readRows();if(stopped.length!==4||stopped.some(x=>x.positionRad!==undefined||x.sampleCurrent!=='false'))throw Error('Reset must clear observed motor samples');
 await mark('reset-cleared-verified');await checkpoint('stopped');await page.waitForTimeout(3000);
 await fs.writeFile(dir+'/assertions.json',JSON.stringify({fourMotorsInitiallyRunning:true,selectedFault1AppliedThroughUI:true,motor1DisabledWhileOthersRun:true,pauseHoldsExactPoseFor5s:true,pauseMarksLastObserved:true,resetClearsSamples:true,finalBeforePause:rows,pausedRows:held,stoppedRows:stopped},null,2));
 await mark('completed');
}catch(e){console.log('FAILED',e.stack);await mark('failed',{error:e.message});await checkpoint('failure').catch(()=>{});process.exitCode=1;}
finally{await Promise.allSettled(pending);await fs.writeFile(dir+'/worker-final.json',JSON.stringify(await page.evaluate(()=>window.__quadWorkers??[]).catch(()=>[]),null,2));if(cadFrame)await fs.writeFile(dir+'/cad-final.json',JSON.stringify(await cadFrame.evaluate(()=>window.__quadFrames??[]).catch(()=>[]),null,2));await ctx.unrouteAll({behavior:'ignoreErrors'});await ctx.close();const videoPath=await page.video().path();console.log('VIDEO',videoPath);await fs.writeFile(dir+'/video.json',JSON.stringify({path:videoPath,sha256:sha(await fs.readFile(videoPath))},null,2));await browser.close();}
