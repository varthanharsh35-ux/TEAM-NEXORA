from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data'
docs=[]
for line in (D/'business_seed.tsv').read_text(encoding='utf8').splitlines():
 cat,text=line.split('\t');docs.append(dict(id='sector-'+cat,source='curated-sector-priors',text=text.replace('|','; '),kind='curated',url=''))
for d in json.loads((D/'districts.json').read_text(encoding='utf8')):
 docs.append(dict(id='district-'+d['id'],source='curated-district-profiles',text=' '.join(d['names'].values())+' '+d['region']+' local economy planning profile; all density and purchasing-power multipliers are estimated.',kind='estimated',url='https://lokbhavan.tn.gov.in/districts-of-tamil-nadu/'))
for p in json.loads((D/'raw/nabard_pages.json').read_text(encoding='utf8')):
 text=p['text']
 for n in range(0,len(text),1600):
  chunk=text[n:n+1800]
  if len(chunk)>150:docs.append(dict(id=f'nabard-{p["page"]}-{n}',source='nabard',text=chunk,page=p['page'],kind='official',url='https://www.nabard.org/auth/writereaddata/tender/pub_0602250348211363.pdf'))
docs.append(dict(id='nsfdc',source='nsfdc',text='Micro Finance Scheme: project cost up to INR 140000, loan up to 90 percent capped at 125000, annual interest 6.5 percent, quarterly repayment within 3 years including 3 months moratorium. Term Loan: project above 140000 up to 5000000, loan capped 4500000, annual interest 8 percent, 7 years including 6 months moratorium. Eligibility must be checked with the channelising agency.',kind='official',url='https://nsfdc.nic.in/faqs'))
(D/'knowledge.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding='utf8');print('RAG chunks',len(docs))
