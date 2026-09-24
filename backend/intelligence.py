from pathlib import Path
import json,re,unicodedata,difflib
from functools import lru_cache
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
def read(name):return json.loads((DATA/name).read_text(encoding='utf8'))
DISTRICTS=read('districts.json');BLOCKS=read('blocks.json');VILLAGES=read('villages.json');SECTORS=read('sectors.json')
MODEL=joblib.load(ROOT/'models/business_classifier.joblib')
def norm(s):
 text=unicodedata.normalize('NFKC',s).casefold()
 return ' '.join(''.join(c if c.isspace() or unicodedata.category(c)[0] in 'LMN' else ' ' for c in text).split())
def district_of(text):
 q=norm(text)
 hits=[]
 for d in DISTRICTS:
  for name in list(d['names'].values())+d['aliases']:
   n=norm(name)
   if re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',q):hits.append((len(n),d))
 return max(hits,key=lambda x:x[0])[1] if hits else None
def coverage_data():
 return {**read('coverage.json'),'district_list':DISTRICTS,'metrics':read('../models/metrics.json')}
def search_locations(q,district=''):
 query=norm(q)
 rows=[dict(name=d['names']['en'],district=d['id'],kind='district',names=d['names']) for d in DISTRICTS]+[dict(b,kind='block') for b in BLOCKS]+[dict(v,kind='village') for v in VILLAGES]
 if district:rows=[r for r in rows if r['district']==district]
 if not query:return rows[:12]
 exact=[r for r in rows if query in norm(r['name']) or any(query in norm(n) for n in r.get('names',{}).values())]
 if exact:return sorted(exact,key=lambda r:(norm(r['name'])!=query,len(r['name'])))[:12]
 return sorted(rows,key=lambda r:difflib.SequenceMatcher(None,query,norm(r['name'])).ratio(),reverse=True)[:5]

def resolve_location(text,chosen=''):
 # Explicit foreign-state names cannot silently acquire Tamil Nadu facts.
 if re.search(r'\b(kerala|karnataka|maharashtra|andhra|telangana|delhi|bihar|gujarat|punjab|west bengal|uttar pradesh|madhya pradesh|rajasthan|odisha|assam|goa)\b',norm(text)) or any(s in text for s in ['கேரளா','கர்நாடகா','மகாராஷ்டிரா','केरल','कर्नाटक','महाराष्ट्र','उत्तर प्रदेश']):
  return {'status':'outside_state','candidates':[]}
 district=next((d for d in DISTRICTS if d['id']==chosen),None) or district_of(text)
 q=norm(text)
 for s in ['tamil nadu','tamilnadu','தமிழ்நாடு','तमिल नाडु','village','block','district']:q=q.replace(s,' ')
 if district:
  for s in list(district['names'].values())+district['aliases']:q=q.replace(norm(s),' ')
 q=' '.join(q.split())
 rows=VILLAGES+BLOCKS
 if district:rows=[r for r in rows if r['district']==district['id']]
 candidates=[]
 if q:
  # Match longest named entity first; ambiguous duplicates require a district.
  candidates=[r for r in rows if re.search(r'(?<!\w)'+re.escape(norm(r['name']))+r'(?!\w)',q)]
  if not candidates:
   top=sorted(((difflib.SequenceMatcher(None,q,norm(r['name'])).ratio(),r) for r in rows),key=lambda x:x[0],reverse=True)[:5]
   candidates=[r for score,r in top if score>=.76 and score>=top[0][0]-.025]
 if candidates:
  maxlen=max(len(r['name']) for r in candidates);candidates=[r for r in candidates if len(r['name'])>=maxlen-2]
  unique={(r['district'],r.get('block',r['name'])):r for r in candidates}
  if len(unique)>1 and not district:return {'status':'ambiguous','candidates':list(unique.values())[:5]}
  r=next(iter(unique.values()));district=next(d for d in DISTRICTS if d['id']==r['district'])
  return {'status':'matched','district':district,'place':r,'granularity':'historical_directory','input':text}
 if not district:
  top=sorted(((max(difflib.SequenceMatcher(None,norm(text),norm(n)).ratio() for n in list(d['names'].values())+d['aliases']),d) for d in DISTRICTS),key=lambda x:x[0],reverse=True)
  if top[0][0]>=.73 and top[0][0]-top[1][0]>.08:district=top[0][1]
 if district:return {'status':'district_proxy' if q else 'matched','district':district,'place':{'name':text,'district':district['id']},'granularity':'district_estimate','input':text}
 return {'status':'clarify','candidates':[]}

def classify(text,override='auto'):
 if override in SECTORS:return {'category':override,'confidence':None,'method':'user','uncertain':override=='other'}
 x=MODEL.named_steps['tfidf'].transform([text]);probs=MODEL.predict_proba([text])[0];i=int(probs.argmax());p=float(probs[i]);cat=str(MODEL.classes_[i])
 uncertain=x.nnz<3 or p<.30
 return {'category':'other' if uncertain else cat,'suggested':cat,'confidence':round(p,3),'method':'trained','uncertain':uncertain}

@lru_cache(maxsize=1)
def rag_index():
 docs=read('knowledge.json')
 vec=TfidfVectorizer(analyzer='char',ngram_range=(2,4),max_features=45000,sublinear_tf=True)
 matrix=vec.fit_transform([d['text'] for d in docs])
 return docs,vec,matrix
def retrieve(query,district,category):
 docs,vec,matrix=rag_index();scores=linear_kernel(vec.transform([query+' '+district+' '+category]),matrix).ravel()
 ids=scores.argsort()[-4:][::-1]
 return [dict(docs[int(i)],score=round(float(scores[i]),3)) for i in ids]
