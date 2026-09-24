const {chromium}=require(process.env.PLAYWRIGHT_PATH);
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await b.newPage();let errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*.tile.openstreetmap.org/**',r=>r.abort());
 await page.route('**/api/geocode?**',r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({location:'Alanganallur, Madurai',district:'Madurai'})}));
 await page.goto('http://127.0.0.1:8000',{waitUntil:'networkidle'});
 await page.locator('.map-toggle').click();await page.locator('.map-surface').click({position:{x:180,y:140}});
 await page.waitForFunction(()=>document.getElementById('location').value==='Alanganallur, Madurai');
 for(const lang of ['ta','hi','en']){
  await page.locator(`.languages button[lang="${lang}"]`).click();
  const labels=JSON.parse(require('fs').readFileSync(`src/locales/${lang}.json`,'utf8'));
  await page.getByRole('button',{name:labels.zoom_in,exact:true}).click();
  await page.getByRole('button',{name:labels.zoom_out,exact:true}).click();
 }
 if(errors.length)throw Error(errors.join('\n'));
 await b.close();console.log('Map selection, unavailable tiles and all-language controls passed (reverse lookup mocked).');
})().catch(e=>{console.error(e);process.exit(1)});
