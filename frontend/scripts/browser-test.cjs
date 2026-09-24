const { chromium }=require(process.env.PLAYWRIGHT_PATH || 'playwright');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
 const out=path.resolve('../audit/browser');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',args:['--disable-gpu']});
 const ctx=await browser.newContext({viewport:{width:1440,height:1000}});
 const page=await ctx.newPage();let errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8000',{waitUntil:'networkidle'});
 await page.screenshot({path:path.join(out,'desktop-intake.png'),fullPage:true});
 await page.getByRole('button',{name:'Try a dairy example',exact:true}).click();
 await page.getByRole('button',{name:'Prepare my business plan',exact:true}).click();
 await page.getByRole('heading',{name:'DairyMadurai'}).waitFor({timeout:30000}).catch(()=>page.locator('.report-header h1').waitFor({timeout:30000}));
 await page.screenshot({path:path.join(out,'desktop-report.png'),fullPage:true});
 await page.getByRole('button',{name:'Financial plan',exact:true}).first().click();
 const metricText=await page.locator('.report-section:not(.screen-hidden) .metrics-grid').innerText();
 if(!metricText.includes('10,00,000')||!metricText.includes('9,00,000'))throw Error('Financial example mismatch: '+metricText);
 if(await page.locator('.repayment-table tbody tr').count()!==28)throw Error('Term schedule must contain 28 quarters');
 await page.screenshot({path:path.join(out,'desktop-finance.png'),fullPage:true});
 for(const lang of ['ta','hi','en']){
  await page.locator(`.languages button[lang="${lang}"]`).click();
  if(await page.locator('html').getAttribute('lang')!==lang)throw Error('document language not updated');
  const file=JSON.parse(fs.readFileSync(`src/locales/${lang}.json`,'utf8'));
  await page.getByRole('heading',{name:file.term,exact:true}).waitFor();
  if(lang!=='en'){
   const visible=await page.locator('body').innerText();
   for(const phrase of ['Project cost','Working capital','Quarterly instalment','Annual interest','No payment'])if(visible.includes(phrase))throw Error(`English leak in ${lang}: ${phrase}`);
  }
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(out,`mobile-finance-${lang}.png`),fullPage:true});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
  if(overflow)throw Error(`Horizontal overflow in ${lang}`);
  await page.emulateMedia({media:'print'});
  await page.pdf({path:path.join(out,`report-${lang}.pdf`),format:'A4',printBackground:true});
  await page.emulateMedia({media:'screen'});
 }
 const amount=page.locator('.adjust input');await amount.fill('14000');
 await page.getByRole('heading',{name:'Micro Finance Scheme',exact:true}).waitFor({timeout:20000});
 if(await page.locator('.repayment-table tbody tr').count()!==12)throw Error('Micro schedule must contain 12 quarters');
 const gap=await page.locator('.report-section:not(.screen-hidden) .metrics-grid').innerText();if(!gap.includes('1,000'))throw Error('Cap funding gap not displayed');
 await amount.fill('500001');await page.getByText('Project cost exceeds ₹50 lakh.',{exact:false}).waitFor({timeout:20000});
 await amount.fill('100000');await page.getByRole('heading',{name:'Term Loan Scheme',exact:true}).waitFor({timeout:20000});
 await page.locator('nav button').first().click();
 await page.locator('.languages button[lang="ta"]').click();
 await page.screenshot({path:path.join(out,'mobile-report-ta.png'),fullPage:true});
 await page.waitForFunction(()=>navigator.serviceWorker.controller!==null);
 await ctx.setOffline(true);await page.reload({waitUntil:'domcontentloaded'});
 await page.locator('.report-header h1').waitFor({timeout:20000});
 await page.screenshot({path:path.join(out,'offline-ta.png'),fullPage:true});
 await ctx.setOffline(false);
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({passed:true,consoleErrors:errors,checks:['English dairy example','all 3 languages','390px horizontal overflow','micro boundary cap','outside limit','28 and 12 quarter schedules','three-language print PDFs','service-worker offline reload']},null,2));
 if(errors.length)throw Error(errors.join('\n'));
 await browser.close();console.log('Browser tests passed. Screenshots and 3 print PDFs saved.');
})().catch(e=>{console.error(e);process.exit(1)});
