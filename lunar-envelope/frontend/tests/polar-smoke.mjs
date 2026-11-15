import assert from 'node:assert/strict';
import {chromium} from 'playwright-core';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(process.env.BASE_URL||'http://127.0.0.1:8000/',{waitUntil:'networkidle',timeout:60000});
 const map=page.getByRole('region',{name:'Explore the surface'});await map.getByText(/Site A · -85.00°, 0.00° · -693 m/).waitFor({timeout:30000});await map.getByRole('button',{name:'Zoom in'}).click();await map.getByRole('button',{name:'Zoom out'}).click();await map.getByRole('button',{name:'Reset view'}).click();
 await map.getByLabel('Overlay').selectOption('none');await map.getByLabel('Overlay').selectOption('elevation');
 await map.getByLabel('Waypoint latitude').fill('-85');await map.getByLabel('Waypoint longitude').fill('0');await map.getByRole('button',{name:'Add waypoint'}).click();
 await map.getByLabel('Waypoint longitude').fill('90');await map.getByRole('button',{name:'Add waypoint'}).click();await map.getByText(/km geometric path/).waitFor({timeout:30000});
 await map.getByLabel('Inspect route profile').fill('3');await map.getByRole('button',{name:'Use last for Site A'}).click();assert.equal(await page.getByRole('spinbutton',{name:'Site A longitude'}).inputValue(),'90');
 const box=await map.locator('canvas').boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+box.width/2+30,box.y+box.height/2+20);await page.mouse.up();
 await map.locator('canvas').click({position:{x:box.width/2,y:box.height/2}});await map.locator('ol li').nth(2).waitFor();
 await page.getByRole('button',{name:'EXOSPHERE LAB'}).click();const chart=page.getByRole('region',{name:'Scenario trends'});await chart.getByRole('button',{name:'Pin current scenario'}).waitFor();await page.waitForFunction(()=>!document.querySelector('.scenario-chart button')?.disabled);await chart.getByRole('button',{name:'Pin current scenario'}).click();await chart.getByLabel('Scenario chart output').selectOption('potential');await chart.getByLabel('Inspect scenario sample').fill('3');await chart.getByRole('button',{name:'Apply this phase'}).click();await chart.getByText('Baseline:',{exact:false}).waitFor();
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);
 console.log('Polar map, route, site application and scenario chart browser checks passed.');
}finally{await browser.close()}
