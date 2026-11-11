const { chromium }=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs'),path=require('path');
const OUT=process.env.CAPTURE_DIR || path.resolve('capture/video');fs.mkdirSync(OUT,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_BIN || '/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--enable-webgl','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 const scenes=[];
 async function scene(name,act){
  const ctx=await browser.newContext({viewport:{width:1600,height:900},deviceScaleFactor:1,recordVideo:{dir:OUT,size:{width:1600,height:900}}});
  const page=await ctx.newPage();page.setDefaultTimeout(6000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const start=Date.now();
  await page.goto('https://app.kernelcad.com/p/DyJ405zg?version=3',{waitUntil:'domcontentloaded',timeout:45000});
  await page.getByRole('button',{name:'Reject',exact:true}).click({timeout:2000}).catch(()=>{});
  await page.getByRole('button',{name:'Exploded view',exact:true}).waitFor({state:'visible',timeout:20000});
  await page.waitForTimeout(4000);
  const content=(await page.locator('body').innerText());
  if(!content.includes('36 bodies')||!content.includes('Ready'))throw Error('KernelCAD geometry not ready');
  const begin=(Date.now()-start)/1000;
  await act(page);
  await page.waitForTimeout(1600);
  await page.screenshot({path:path.join(OUT,name+'.png')});
  const end=(Date.now()-start)/1000;
  await ctx.close();const dest=path.join(OUT,name+'.webm');fs.renameSync(await page.video().path(),dest);
  scenes.push({name,file:dest,start:begin,end,errors,model:'DyJ405zg',revision:3});fs.writeFileSync(path.join(OUT,'cad-scenes.json'),JSON.stringify(scenes,null,2));console.log('RECORDED',JSON.stringify(scenes.at(-1)));
 }
 async function orbit(page,dx,dy,n=50){const b=await page.locator('canvas').first().boundingBox();if(!b)throw Error('No canvas');const x=b.x+b.width*.5,y=b.y+b.height*.52;await page.mouse.move(x,y);await page.mouse.down();for(let i=1;i<=n;i++){await page.mouse.move(x+dx*i/n,y+dy*Math.sin(i/n*Math.PI));await page.waitForTimeout(34)}await page.mouse.up();}
 await scene('01-design',async p=>{
  await p.getByRole('button',{name:'Close model tree',exact:true}).click();
  await p.getByRole('tab',{name:'Code',exact:true}).click();
  await p.getByRole('button',{name:'Dimensions',exact:true}).click();
  await p.waitForTimeout(1700);await orbit(p,110,22,60);await p.waitForTimeout(1500);
 });
 await scene('02-assembly',async p=>{
  await p.getByRole('button',{name:'Close model tree',exact:true}).click();
  await p.getByRole('button',{name:'Hide inspector panel',exact:true}).click();
  await p.getByRole('button',{name:'Exploded view',exact:true}).click();
  const slider=p.getByRole('slider',{name:'Explode distance',exact:true});
  await slider.waitFor({state:'visible'});console.log('EXPLODE',await slider.getAttribute('min'),await slider.getAttribute('max'),await slider.inputValue());
  await slider.focus();await slider.press('Home');
  for(let i=0;i<12;i++){await slider.press('ArrowRight');await p.waitForTimeout(90)}
  await orbit(p,105,24,55);await p.waitForTimeout(1600);
  for(let i=0;i<12;i++){await slider.press('ArrowLeft');await p.waitForTimeout(90)}
  await p.getByRole('button',{name:'Exploded view',exact:true}).click();await p.waitForTimeout(1700);
 });
 await scene('03-hero',async p=>{
  await p.getByRole('button',{name:'Close model tree',exact:true}).click();await p.getByRole('button',{name:'Hide inspector panel',exact:true}).click();await orbit(p,155,35,100);await p.waitForTimeout(1000);
 });
 await browser.close();
})().catch(e=>{console.error(e.stack);process.exit(1)});
