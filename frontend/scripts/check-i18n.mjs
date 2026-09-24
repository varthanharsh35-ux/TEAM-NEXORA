import fs from 'node:fs';
const languages=['en','ta','hi'];const data=Object.fromEntries(languages.map(l=>[l,JSON.parse(fs.readFileSync(`src/locales/${l}.json`,'utf8'))]));
const base=Object.keys(data.en).sort();let errors=[];
for(const lang of languages){if(JSON.stringify(Object.keys(data[lang]).sort())!==JSON.stringify(base))errors.push(`${lang}: key mismatch`);for(const key of base){const value=data[lang][key];if(!value?.trim())errors.push(`${lang}:${key}: empty`);const vars=s=>JSON.stringify((s.match(/\{\{\w+\}\}/g)||[]).sort());if(vars(value)!==vars(data.en[key]))errors.push(`${lang}:${key}: interpolation mismatch`);if(lang!=='en'&&!['english','tamil','hindi'].includes(key)&&value===data.en[key])errors.push(`${lang}:${key}: English copy`);}}
const source=fs.readdirSync('src').filter(f=>f.endsWith('.jsx')).map(f=>fs.readFileSync(`src/${f}`,'utf8')).join('\n');
if(/Ã¢|Ã‚|â€|Â·/.test(source))errors.push('Broken UTF-8 punctuation in JSX');
for(const [,key] of source.matchAll(/\bt\('([^']+)'/g))if(!data.en[key])errors.push(`missing referenced key ${key}`);
// Static user-visible JSX text must be a translated expression; decorative numbers/arrows are allowed.
for(const [,text] of source.matchAll(/(?:<[A-Za-z][^<>]*>|<\/[A-Za-z][^>]*>)([^<>{}\n]+)</g))if(/[A-Za-z]{2,}/.test(text.trim())&&!text.includes('=>')&&text.trim()!=='OpenStreetMap')errors.push(`hardcoded JSX: ${text.trim()}`);
if(errors.length){console.error(errors.join('\n'));process.exit(1)}console.log(`PASS: ${base.length} keys × 3 languages; placeholders, references and JSX text checked.`);

