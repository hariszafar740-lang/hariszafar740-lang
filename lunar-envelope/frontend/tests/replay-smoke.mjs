import assert from 'node:assert/strict';
import {chromium} from 'playwright-core';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:900}});
try{
 await page.goto(process.env.BASE_URL||'http://127.0.0.1:8000/',{waitUntil:'networkidle'});
 const sky=page.getByRole('region',{name:'Sky geometry playback'});await sky.waitFor();
 const skyRange=sky.getByRole('slider');assert.equal(await skyRange.inputValue(),'0');
 await sky.getByRole('button',{name:'Step forward'}).click();assert.equal(await skyRange.inputValue(),'1');
 await sky.getByRole('button',{name:'Play',exact:true}).click();await sky.getByRole('button',{name:'Pause'}).waitFor();await page.waitForTimeout(1200);assert.ok(Number(await skyRange.inputValue())>=2);
 await sky.getByRole('button',{name:'Pause'}).click();await sky.getByRole('button',{name:'Reset time'}).click();assert.equal(await skyRange.inputValue(),'0');
 await skyRange.fill('3');assert.equal(await skyRange.inputValue(),'3');
 await page.getByRole('button',{name:'EXOSPHERE LAB'}).click();
 const phase=page.getByRole('region',{name:'Lunar phase playback'});await phase.waitFor();
 const range=phase.getByRole('slider');const initial=Number(await range.inputValue());
 const response=page.waitForResponse(r=>r.url().endsWith('/api/simulate')&&r.request().method()==='POST'&&r.ok());
 await phase.getByRole('button',{name:'Step forward'}).click();assert.ok(Number(await range.inputValue())>initial);await response;
 await phase.getByRole('button',{name:'Play',exact:true}).click();await phase.getByRole('button',{name:'Pause'}).waitFor();await page.waitForTimeout(1200);await phase.getByRole('button',{name:'Pause'}).click();
 await phase.getByRole('button',{name:'Reset time'}).click();assert.equal(await range.inputValue(),'0');
 await range.fill('10');assert.equal(await range.inputValue(),'10');
 await page.setViewportSize({width:390,height:844});await page.reload({waitUntil:'networkidle'});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 console.log('Playback controls, backend response and mobile overflow checks passed.');
}finally{await browser.close()}
