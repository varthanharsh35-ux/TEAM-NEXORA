"""User-triggered map lookups; persistent last-good cache, no invented POIs."""
import json,os,sqlite3,time,threading
from contextlib import closing
from pathlib import Path
import httpx
from fastapi import HTTPException
from intelligence import district_of,norm
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data/maps.sqlite3'
LOCK=threading.Lock();LAST=0
def cached(key,value=None):
 with closing(sqlite3.connect(DB)) as c:
  c.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY,body TEXT,updated REAL)')
  if value is not None:c.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',(key,json.dumps(value),time.time()));c.commit();return value
  row=c.execute('SELECT body,updated FROM cache WHERE key=?',(key,)).fetchone()
  return (json.loads(row[0]),row[1]) if row else None
def unpack(row):
 if row.get('address',{}).get('state')!='Tamil Nadu':return None
 d=district_of(row.get('display_name',''))
 return {'location':row['display_name'][:200],'lat':float(row['lat']),'lon':float(row['lon']),'district':d['id'] if d else '', 'source':'OpenStreetMap','source_url':f"https://www.openstreetmap.org/{row['osm_type']}/{row['osm_id']}"}
def search(q):
 global LAST
 key='search:'+norm(q);old=cached(key)
 if old and time.time()-old[1]<30*86400:return {'items':old[0],'cached':True}
 try:
  import main
  with main.GEOCODE_LOCK:
   if time.monotonic()-main.GEOCODE_LAST<1:raise HTTPException(429,detail='map_wait')
   main.GEOCODE_LAST=time.monotonic()
  with httpx.Client(timeout=12) as c:
   r=c.get(os.getenv('GEOCODER_URL','https://nominatim.openstreetmap.org')+'/search',params={'q':q if 'tamil' in q.lower() else q+', Tamil Nadu, India','format':'jsonv2','addressdetails':1,'countrycodes':'in','limit':5},headers={'User-Agent':'GramSahayak-SIH26091-prototype/2.0'})
   r.raise_for_status();items=[x for row in r.json() if (x:=unpack(row))]
  cached(key,items);return {'items':items,'cached':False}
 except HTTPException:raise
 except Exception:
  if old:return {'items':old[0],'cached':True,'stale':True}
  raise HTTPException(503,detail='map_failed')

TAGS={'dairy':'["shop"~"dairy|convenience|supermarket"]','retail':'["shop"~"convenience|supermarket|general"]','food':'["amenity"~"restaurant|cafe|fast_food"]','tailoring':'["shop"~"tailor|clothes"]','agriculture':'["shop"~"agrarian|farm"]','poultry':'["shop"="butcher"]','fish':'["shop"="seafood"]','repair':'["shop"~"car_repair|bicycle|electronics"]','craft':'["shop"~"craft|gift"]','manufacturing':'["craft"]','transport':'["amenity"="taxi"]','services':'["shop"~"hairdresser|beauty|laundry"]','other':'["shop"]'}
def nearby(lat,lon,category):
 global LAST
 key=f'nearby:{lat:.4f}:{lon:.4f}:{category}';old=cached(key)
 if old and time.time()-old[1]<7*86400:return {**old[0],'cached':True}
 try:
  with LOCK:
   if time.monotonic()-LAST<2:raise HTTPException(429,detail='map_wait')
   LAST=time.monotonic()
  tag=TAGS.get(category,TAGS['other']);around=f'(around:15000,{lat},{lon})'
  query=f'[out:json][timeout:12];(nwr["amenity"~"bank|post_office"]{around};nwr{tag}{around};);out center 250;'
  with httpx.Client(timeout=16) as c:
   r=c.get(os.getenv('OVERPASS_URL','https://overpass-api.de/api/interpreter'),params={'data':query},headers={'User-Agent':'GramSahayak-SIH26091-prototype/2.0'});r.raise_for_status();raw=r.json()
  points=[]
  for item in raw.get('elements',[]):
   tags=item.get('tags',{});coords=item.get('center',item)
   if 'lat' not in coords:continue
   kind=tags.get('amenity') if tags.get('amenity') in ['bank','post_office'] else 'competitor'
   points.append({'id':f"{item['type']}/{item['id']}",'lat':coords['lat'],'lon':coords['lon'],'name':tags.get('name',''),'names':{l:tags.get('name:'+l,tags.get('name','')) for l in ['en','ta','hi']},'kind':kind,'schemes':[]})
  result={'points':points,'checked':time.strftime('%Y-%m-%d'),'source':'OpenStreetMap','complete':False,'cached':False}
  cached(key,result);return result
 except HTTPException:raise
 except Exception:
  if old:return {**old[0],'cached':True,'stale':True}
  raise HTTPException(503,detail='map_failed')
