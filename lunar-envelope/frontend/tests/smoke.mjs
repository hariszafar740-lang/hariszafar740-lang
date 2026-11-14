import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';

const executablePath=process.env.CHROMIUM_PATH;
if (!executablePath) throw new Error('Set CHROMIUM_PATH to a Chromium executable; start the app on port 8000 first.');
const browser=await chromium.launch({executablePath,headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:900},acceptDownloads:true});
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
try {
  await page.goto(process.env.BASE_URL || 'http://127.0.0.1:8000/',{waitUntil:'networkidle'});
  await page.getByText('30-DAY SCENARIO SCREENING').waitFor();
  await page.getByRole('button',{name:'GUIDED TOUR'}).click();
  await page.getByText('Choose a landing site').waitFor();
  await page.getByRole('button',{name:'NEXT STEP'}).click();
  await page.getByText('Explore lunar conditions').waitFor();
  await page.getByRole('button',{name:'Close guided tour'}).click();
  const latitude = page.getByRole('spinbutton',{name:'LATITUDE in degrees, press Enter to apply'});
  await latitude.fill('-87.5');
  await latitude.press('Enter');
  await page.getByText('87.5° S', { exact: false }).first().waitFor();
  await page.getByRole('button',{name:'GO TO SAMPLE SITE'}).click();
  await page.getByText('MODEL AT APPROX. SAME LOCAL TIME').waitFor();
  assert.match(await page.locator('.observation-value').innerText(), /80\.4/);
  const [csv]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'CSV'}).click()]);
  assert.equal(csv.suggestedFilename(),'lunar-mission-brief.csv');
  const [pdf]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'PDF'}).click()]);
  assert.equal(pdf.suggestedFilename(),'lunar-mission-brief.pdf');
  await page.setViewportSize({width:390,height:844});
  await page.reload({waitUntil:'networkidle'});
  await page.getByRole('button',{name:'Toggle controls'}).click();
  await page.getByText('Lunar phase',{exact:true}).waitFor();
  assert.equal(await page.getByRole('button',{name:'PDF'}).isVisible(),true);
  assert.deepEqual(errors,[]);
  console.log('Desktop and mobile browser smoke checks passed.');
} finally { await browser.close(); }
