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
  await page.getByText('Find your window').waitFor();
  await page.keyboard.press('Tab');
  assert.equal(await page.locator(':focus').innerText(),'Skip to comparison');
  await page.keyboard.press('Enter');
  assert.equal(await page.locator(':focus').getAttribute('id'),'nav-main');
  await page.getByText('LOCAL SKY GEOMETRY').waitFor();
  assert.equal(await page.locator('.navigator').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(8, 13, 28)');
  await page.getByRole('heading',{name:'One Moon. Different horizons.'}).waitFor();
  await page.getByRole('spinbutton',{name:'Duration in days'}).fill('3');
  await page.getByRole('button',{name:'RUN EXAMPLE COMPARISON'}).click();
  await page.getByText('MISSION WINDOW / 7 DAYS').waitFor();
  assert.equal(await page.getByRole('spinbutton',{name:'Duration in days'}).inputValue(),'7');
  assert.equal(await page.locator('.compare-card').count(),2);
  await page.getByRole('heading',{name:'What the numbers mean.'}).waitFor();
  assert.match(await page.locator('.model-boundaries').innerText(),/separate calculation/);
  assert.match(await page.locator('.model-boundaries').innerText(),/60-minute midpoint/);
  assert.match(await page.locator('.compare-card').first().innerText(),/sensitivity test, not uncertainty/);
  const provenance=page.getByRole('link',{name:'METHOD & PROVENANCE'});
  assert.equal(await provenance.getAttribute('href'),'/api/provenance/ephemeris');
  const provenanceResponse=await page.request.get(new URL('/api/provenance/ephemeris',page.url()).href);
  assert.equal(provenanceResponse.status(),200);
  assert.match(await provenanceResponse.text(),/Lunar geometry data, provenance and validation/);
  assert.match(await page.locator('.nav-footer').innerText(),/HARIS ZAFAR/);
  assert.equal(await page.locator('.compare-card').count(),2);
  const contrast=await page.evaluate(()=>{
    const color=s=>s.match(/[\d.]+/g).slice(0,3).map(Number)
      .map(v=>v/255)
      .map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
    const lum=s=>{
      const v=color(s);
      return .2126*v[0]+.7152*v[1]+.0722*v[2];
    };
    const check=(fg,bg)=>{
      const a=lum(getComputedStyle(document.querySelector(fg)).color);
      const b=lum(getComputedStyle(document.querySelector(bg)).backgroundColor);
      return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    };
    return [
      check('.nav-metric strong','.compare-card'),
      check('.run-plan','.run-plan')
    ];
  });
  assert.ok(
    contrast.every(value=>value>=4.5),
    `Rendered text contrast failed: ${contrast}`
  );
  await page.getByText(
    'Timeline key: solid bright segments',
    {exact:false}
  ).first().waitFor();
  await page.getByRole('button',{name:'SAMPLE SITE A TERRAIN'}).click();
  await page.getByText('Sun above sampled:',{exact:false}).waitFor({timeout:30000});
  await page.getByText('crosshatching means unknown azimuth',{exact:false}).waitFor();
  assert.match(await page.locator('.terrain-result').innerText(),/not confirmed visibility/);
  const [terrainJson]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'DOWNLOAD TERRAIN JSON'}).click()]);
  const terrainData=JSON.parse(await (await import('node:fs/promises')).readFile(await terrainJson.path(),'utf8'));
  assert.equal(terrainData.horizon_deg.length,360);
  assert.equal(terrainData.observer_height_m,2);
  assert.equal(terrainData.max_distance_km,300);
  assert.equal(terrainData.sensitivity_offset_deg,1);
  assert.equal(terrainData.peak_distance_km.length,360);
  assert.match(await page.locator('.terrain-result').innerText(),/not a measured uncertainty/);
  await page.getByRole('combobox',{name:'Terrain raster resolution'}).selectOption('native');
  await page.getByRole('button',{name:'SAMPLE SITE A TERRAIN'}).click();
  await page.getByRole('alert').filter({hasText:'Native LOLA rasters'}).waitFor();
  await page.getByRole('combobox',{name:'Terrain raster resolution'}).selectOption('coarse');
  await page.getByRole('spinbutton',{name:'Observer height above terrain in meters'}).fill('10');
  await page.getByText('Terrain inputs changed.',{exact:false}).waitFor();
  await page.getByRole('button',{name:'PIN CURRENT AS BASELINE'}).click();
  await page.getByText('BASELINE', {exact:true}).waitFor();
  await page.getByRole('slider',{name:'Sky time'}).fill('2');
  assert.match(await page.locator('.time-scrub').innerText(),/BIN MIDPOINT/);
  await page.getByRole('button',{name:'Site B',exact:true}).click();
  assert.match(await page.locator('.plot-note').innerText(),/SITE B/);
  await page.getByRole('spinbutton',{name:'Duration in days'}).fill('3');
  await page.getByText('Inputs changed. Displayed results',{exact:false}).waitFor();
  await page.getByLabel('Bin size in minutes').selectOption('15');
  await page.getByRole('spinbutton',{name:'Sun clearance in degrees'}).fill('1');
  await page.getByRole('button',{name:'+ ADD THIRD SITE'}).click();
  assert.equal(await page.getByRole('spinbutton',{name:'Site C latitude'}).count(),1);
  await page.getByRole('button',{name:'REMOVE SITE C'}).click();
  assert.match(await page.locator('.nav-section-heading .nav-label').innerText(),/7 DAYS/);
  await page.getByRole('button',{name:'COMPARE SCENARIOS'}).click();
  await page.getByText('MISSION WINDOW / 3 DAYS').waitFor();
  assert.equal(await page.locator('.nav-main > .draft-notice').count(),0);
  await page.getByText('REFINED GEOMETRIC TRANSITIONS').click();
  await page.getByText('15-minute sign scan',{exact:false}).waitFor();
  await page.getByLabel('Start date and time UTC').fill('2028-01-01T00:00');
  await page.getByRole('spinbutton',{name:'Site A observer height in meters'}).fill('100');
  await page.getByRole('button',{name:'COMPARE SCENARIOS'}).click();
  await page.getByText('No unique coordinate match').waitFor();
  assert.match(await page.locator('.plot-note').innerText(),/2028-01-01/);
  const [json]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'EXPORT JSON'}).click()]);
  assert.equal(json.suggestedFilename(),'lunaris-site-comparison.json');
  const result=JSON.parse(await (await import('node:fs/promises')).readFile(await json.path(),'utf8'));
  assert.equal(result.schema,'lunaris-site-comparison-v1');
  assert.equal(result.manifest.code_revision,null);
  assert.match(result.manifest.terrain,/separate/);
  assert.ok(result.change_summary);
  assert.equal(result.current.step_minutes,15);
  assert.equal(result.current.start,'2028-01-01T00:00:00Z');
  assert.equal(result.current.sites[0].height_m,100);
  assert.ok(result.current.sites[0].refined);
  assert.equal(result.current.dataset_kind,'extended');
  assert.equal(result.current.sun_clearance_deg,1);
  assert.equal(result.current.assumptions.radius_km,1737.4);
  assert.match(result.current.assumptions.corrections,/no light-time/);
  assert.equal(result.current.sites[0].timeline.length,288);
  assert.equal(result.baseline.step_minutes,60);
  assert.match(result.current.dataset_sha256,/^[0-9a-f]{64}$/);
  await page.evaluate(()=>{window.print=()=>{document.body.dataset.printRequested='yes'}});
  await page.getByRole('button',{name:'PRINT / SAVE PDF'}).click();
  assert.equal(await page.locator('body').getAttribute('data-print-requested'),'yes');
  await page.getByRole('button',{name:'CLEAR',exact:true}).click();
  await page.getByText('No baseline pinned yet.',{exact:false}).waitFor();
  await page.getByText('APPROXIMATE SCREENING INTERVALS').click();
  await page.getByText('DATA SOURCES & LIVE STATUS').click();
  await page.getByText('LRO LOLA terrain').waitFor();
  await page.getByRole('button',{name:'CHECK NASA DONKI'}).click();
  await page.getByText('Live NASA DONKI connection disabled.',{exact:false}).waitFor();
  await page.getByRole('button',{name:'EXOSPHERE LAB'}).click();
  await page.getByText('NASA SVS LROC-derived imagery · visual only').waitFor();
  await page.getByText('VISUAL LIGHTING · NOT A FORECAST').waitFor();
  await page.getByRole('button',{name:'Zoom in on globe'}).click();
  await page.getByRole('button',{name:'Zoom out on globe'}).click();
  await page.getByRole('button',{name:'Reset globe view'}).click();
  const initialCoordinates=await page.locator('.viewport-bottom b').innerText();
  await page.locator('.globe-canvas canvas').click();
  await page.waitForFunction(
    previous=>document.querySelector('.viewport-bottom b')?.textContent?.trim()!==previous.trim(),
    initialCoordinates
  );
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
  await page.getByRole('button',{name:'SITE NAVIGATOR'}).click();
  await page.getByText(
    'Site A uses coordinates from the Exosphere Lab.',
    {exact:false}
  ).waitFor();
  assert.equal(
    await page.getByRole('spinbutton',{name:'Site A latitude'}).inputValue(),
    '-88.6'
  );
  assert.equal(
    await page.getByRole('spinbutton',{name:'Site A longitude'}).inputValue(),
    '-69.3'
  );
  await page.getByText('LOCAL SKY GEOMETRY').waitFor();
  const handoff=page.locator('.compare-card').first();
  assert.match(await handoff.innerText(),/-88.6/);
  await page.setViewportSize({width:390,height:844});
  await page.reload({waitUntil:'networkidle'});
  await page.getByText('Find your window').waitFor();
  await page.getByText('LOCAL SKY GEOMETRY').waitFor();
  assert.equal(await page.locator('.compare-card').count(),2);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.getByRole('button',{name:'SAMPLE SITE A TERRAIN'}).click();
  await page.getByText('Sun above sampled:',{exact:false}).waitFor({timeout:30000});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.getByRole('button',{name:'EXOSPHERE LAB'}).click();
  await page.getByRole('button',{name:'Toggle controls'}).click();
  await page.getByText('Lunar phase',{exact:true}).waitFor();
  assert.equal(await page.getByRole('button',{name:'PDF'}).isVisible(),true);
  const fallbackPage=await browser.newPage();
  await fallbackPage.route('**/assets/lroc_color_2k-*.jpg',route=>route.abort());
  await fallbackPage.goto(process.env.BASE_URL || 'http://127.0.0.1:8000/',{waitUntil:'networkidle'});
  await fallbackPage.getByRole('button',{name:'EXOSPHERE LAB'}).click();
  await fallbackPage.getByText('Illustrative fallback · NASA imagery unavailable').waitFor();
  await fallbackPage.close();
  const noWebgl=await browser.newPage();
  await noWebgl.addInitScript(()=>{
    const original=HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext=function(type,...args){
      if(type==='webgl'||type==='webgl2'||type==='experimental-webgl')return null;
      return original.call(this,type,...args);
    };
  });
  await noWebgl.goto(
    process.env.BASE_URL || 'http://127.0.0.1:8000/',
    {waitUntil:'networkidle'}
  );
  await noWebgl.getByRole('button',{name:'EXOSPHERE LAB'}).click();
  await noWebgl.getByText('3D view unavailable.',{exact:false}).waitFor();
  assert.equal(
    await noWebgl.getByRole('spinbutton',{
      name:'LATITUDE in degrees, press Enter to apply'
    }).isVisible(),
    true
  );
  await noWebgl.close();
  assert.deepEqual(errors,[]);
  console.log('Desktop and mobile browser smoke checks passed.');
} finally { await browser.close(); }
