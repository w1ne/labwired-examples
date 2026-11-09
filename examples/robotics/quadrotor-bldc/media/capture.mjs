// Real browser video capture. No synthetic serial output or simulated 3D footage.
import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
const out = path.resolve(process.argv[2] ?? 'artifacts/quadrotor-video');
await fs.mkdir(out,{recursive:true});
const browser = await chromium.launch({
 executablePath:process.env.CHROME_PATH??'/usr/bin/google-chrome',
 headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--enable-webgl',
 '--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader',
 '--disable-background-timer-throttling','--disable-renderer-backgrounding']
});
const opts={viewport:{width:1280,height:720},deviceScaleFactor:1,recordVideo:{dir:out,size:{width:1280,height:720}}};
const shots=[];
async function recordScene(name,url,action){
 const ctx=await browser.newContext(opts), page=await ctx.newPage();
 page.on('pageerror',e=>console.warn('PAGE_ERROR',name,e.message.slice(0,180)));
 console.log('START',name);
 await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
 await page.waitForTimeout(4500);
 await action(page);
 await page.waitForTimeout(1600);
 await ctx.close();
 const src=await page.video().path(),dest=path.join(out,name+'.webm');
 await fs.rename(src,dest);shots.push(dest);
 console.log('COMPLETED',name,(await fs.stat(dest)).size);
}
const kc='https://app.kernelcad.com/embed/DyJ405zg?revision=2';
const lw='https://app.labwired.com/?share=15By9JQ39JOy&embed=true&run=1';
try{
 await recordScene('01-kernelcad',kc,async page=>{
  const cv=page.locator('canvas').first();await cv.waitFor({state:'visible',timeout:20000});
  const b=await cv.boundingBox();
  if(b){const x=b.x+b.width*.54,y=b.y+b.height*.53;
   await page.mouse.move(x,y); await page.mouse.down();
   for(let i=0;i<65;i++){await page.mouse.move(x+Math.sin(i/65*Math.PI)*185,y+Math.sin(i/65*Math.PI)*50);await page.waitForTimeout(42)}
   await page.mouse.up();
  } await page.waitForTimeout(1900);
 });
 await recordScene('02-simulation',lw,async page=>{
  await page.getByText('Serial',{exact:true}).last().click({timeout:15000});
  await page.waitForTimeout(4500);
  const t=await page.locator('body').innerText();
  console.log('SERIAL_READINESS',{boot:t.includes('BLDC READY'),target:t.includes('TARGET REACHED')});
 });
 await recordScene('03-fault-injection',lw,async page=>{
  await page.getByText('Inputs',{exact:true}).last().click({timeout:15000});
  await page.waitForTimeout(1500);
  const slider=page.locator('input[type=range]').first();
  await slider.focus();await slider.press('End');console.log('FAULT_INPUT',await slider.inputValue());
  await page.waitForTimeout(2500);
  await page.getByText('Serial',{exact:true}).last().click({timeout:15000});
  await page.waitForTimeout(3500);
  const t=await page.locator('body').innerText();console.log('FAULT_SERIAL',t.slice(-420).replaceAll('\n',' / '));
  if(!t.includes('FAULT DRIVER')||!t.includes('INVERTER OFF'))throw new Error('Actual Studio failed to show firmware fault/shutdown markers');
 });
 await recordScene('04-final-cad','https://app.kernelcad.com/p/DyJ405zg?version=2',async page=>{
  await page.getByRole('button',{name:'Reject',exact:true}).click({timeout:2500}).catch(()=>{});
  await page.waitForTimeout(2100);
  const b=await page.locator('canvas').first().boundingBox();
  if(b){const x=b.x+b.width*.5,y=b.y+b.height*.49;
   await page.mouse.move(x,y); await page.mouse.down();
   for(let i=0;i<48;i++){await page.mouse.move(x+i*1.45,y+i*.3);await page.waitForTimeout(40)}
   await page.mouse.up();
  }
 });
 console.log('ALL_SCENES',shots);
}catch(e){console.error('CAPTURE_FAILED',e.message);process.exitCode=1}
finally{await browser.close()}
