"""Rebuild local data from cached official directory extracts and explicit estimates."""
from pathlib import Path
import re,json,csv
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
def save(name,obj): (DATA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
names='''Ariyalur|அரியலூர்|अरियालूर
Chengalpattu|செங்கல்பட்டு|चेंगलपट्टु
Chennai|சென்னை|चेन्नई
Coimbatore|கோயம்புத்தூர்|कोयंबटूर
Cuddalore|கடலூர்|कडलूर
Dharmapuri|தருமபுரி|धर्मपुरी
Dindigul|திண்டுக்கல்|डिंडीगुल
Erode|ஈரோடு|ईरोड
Kallakurichi|கள்ளக்குறிச்சி|कल्लाकुरिची
Kanchipuram|காஞ்சிபுரம்|कांचीपुरम
Kanniyakumari|கன்னியாகுமரி|कन्याकुमारी
Karur|கரூர்|करूर
Krishnagiri|கிருஷ்ணகிரி|कृष्णगिरि
Madurai|மதுரை|मदुरै
Mayiladuthurai|மயிலாடுதுறை|मयिलाडुतुरै
Nagapattinam|நாகப்பட்டினம்|नागपट्टिनम
Namakkal|நாமக்கல்|नामक्कल
Nilgiris|நீலகிரி|नीलगिरि
Perambalur|பெரம்பலூர்|पेरम्बलूर
Pudukkottai|புதுக்கோட்டை|पुदुक्कोट्टै
Ramanathapuram|இராமநாதபுரம்|रामनाथपुरम
Ranipet|இராணிப்பேட்டை|रानीपेट
Salem|சேலம்|सेलम
Sivagangai|சிவகங்கை|शिवगंगा
Tenkasi|தென்காசி|तेनकाशी
Thanjavur|தஞ்சாவூர்|तंजावुर
Theni|தேனி|तेनी
Thoothukudi|தூத்துக்குடி|तूत्तुक्कुडी
Tiruchirappalli|திருச்சிராப்பள்ளி|तिरुचिरापल्ली
Tirunelveli|திருநெல்வேலி|तिरुनेलवेली
Tirupathur|திருப்பத்தூர்|तिरुपत्तूर
Tiruppur|திருப்பூர்|तिरुप्पूर
Tiruvallur|திருவள்ளூர்|तिरुवल्लूर
Tiruvannamalai|திருவண்ணாமலை|तिरुवन्नामलै
Tiruvarur|திருவாரூர்|तिरुवारूर
Viluppuram|விழுப்புரம்|विलुप्पुरम
Virudhunagar|விருதுநகர்|विरुधुनगर
Vellore|வேலூர்|वेल्लोर'''
districts=[]
aliases={'Kanchipuram':['kancheepuram','kanchipuram'],'Kanniyakumari':['kanyakumari','nagercoil'],'Tiruchirappalli':['trichy','tiruchi','trichirapalli'],'Coimbatore':['kovai','coimbatore'],'Nilgiris':['the nilgiris','ooty','udhagai'],'Thoothukudi':['tuticorin','thoothukkudi'],'Viluppuram':['villupuram'],'Tirupathur':['tiruppathur','thirupathur'],'Tiruvallur':['thiruvallur'],'Tiruvarur':['thiruvarur']}
for line in names.splitlines():
 en,ta,hi=line.split('|');region='interior'
 if en in ['Thanjavur','Tiruvarur','Mayiladuthurai','Nagapattinam','Ariyalur']:region='delta'
 if en in ['Coimbatore','Tiruppur','Erode','Karur','Namakkal','Salem']:region='industrial'
 if en in ['Thoothukudi','Ramanathapuram','Cuddalore','Kanniyakumari','Chengalpattu']:region='coastal'
 if en in ['Nilgiris','Theni','Dindigul']:region='hills'
 if en in ['Chennai','Tiruvallur','Kanchipuram']:region='urban'
 districts.append(dict(id=en,names={'en':en,'ta':ta,'hi':hi},aliases=aliases.get(en,[]),region=region,density_estimate={'interior':260,'delta':320,'industrial':420,'coastal':290,'hills':170,'urban':650}[region],purchasing_index_estimate={'interior':.88,'delta':.92,'industrial':1.08,'coastal':.94,'hills':.98,'urban':1.18}[region],source='curated-district-profiles',estimated=True))
save('districts.json',districts)
canon={'The Nilgiris':'Nilgiris','Villupuram':'Viluppuram','Thoothukkudi':'Thoothukudi'}
splits={
 'Chengalpattu':['Thiruporur','Kattankolathur','Thirukalukundram','Thomas Malai','Acharapakkam','Madurantakam','Lathur','Chithamur'],
 'Kallakurichi':['Tirukoilur','Tirunavalur','Ulundurpet','Kallakurichi','Chinnasalem','Rishivandiyam','Sankarapuram','Thiyagadurgam','Kalrayan Hills'],
 'Ranipet':['Walajah','Sholinghur','Arakonam','Nemili','Kaveripakkam','Arcot','Thimiri'],
 'Tirupathur':['Madhanur','Thirupathur','Jolarpet','Kandhili','Natrampalli','Alangayam'],
 'Mayiladuthurai':['Mayiladuthurai','Kuthalam','Sembanarkoil','Sirkali','Kollidam'],
 'Tenkasi':['Melaneelithanallur','Kuruvikulam','Sankarankoil','Kadayam','Alankulam','Keelapavoor','Kadayanallur','Shencottai','Tenkasi','Vasudevanallur']}
def current(d,b):
 for dst,blocks in splits.items():
  if b in blocks:return dst
 return canon.get(d,d)
text=(DATA/'raw/Blocks.txt').read_text(encoding='utf-8')
lines=[x.strip() for x in text.splitlines() if x.strip() and not x.startswith(('List of','District Code','Page '))]
blocks=[];d='';pending=''
for line in lines:
 if line.isdigit():pending=line;continue
 if pending:line=pending+' '+line;pending=''
 m=re.match(r'^(\d+) ([A-Za-z ]+?) (\d+) (.+)$',line)
 if m:dc,d,bc,b=m.groups()
 else:
  m=re.match(r'^(\d+) (.+)$',line)
  if not m:continue
  bc,b=m.groups()
 b=b.strip();d=d.strip()
 blocks.append(dict(id=f'{dc}-{bc}',name=b,district=current(d,b),historical_district=d,source='tnrd-blocks',boundary_status='historical-with-curated-crosswalk'))
save('blocks.json',blocks)
blockmap={(b['historical_district'],b['name']):b for b in blocks}
villages=[];d=b='';skipped=[]
for raw in (DATA/'raw/Villages.txt').read_text(encoding='utf-8').splitlines():
 line=' '.join(raw.split())
 if not line or line.startswith(('List of','District Code','Page ')):continue
 m=re.match(r'^(\d+) ([A-Za-z ]+?) (\d+) ([A-Za-z(). /]+?) (\d+) (.+)$',line)
 if m:dc,d,bc,b,vc,v=m.groups()
 else:
  m=re.match(r'^(\d+) ([A-Za-z(). /]+?) (\d+) (.+)$',line)
  if m and (d,m.group(2).strip()) in blockmap:bc,b,vc,v=m.groups()
  else:
   m=re.match(r'^(\d+) (.+)$',line)
   if not m:skipped.append(line);continue
   vc,v=m.groups()
 if (d,b) not in blockmap:skipped.append(line);continue
 villages.append(dict(id=f'{dc}-{bc}-{vc}',name=v,block=b,district=current(d,b),source='tnrd-villages'))
save('villages.json',villages)
save('coverage.json',dict(districts=len(districts),blocks=len(blocks),villages=len(villages),directory_status='historical',crosswalk_status='curated-needs-current-LGD-verification',unparsed_rows=skipped))

# Explicit synthetic planning priors: no claim of observed district prices/competition.
sectors={
 'dairy':(52,36,9000,120,140000,'litre',.15,3),
 'retail':(50,40,8000,180,75000,'basket',.25,8),
 'food':(35,18,11000,140,90000,'serving',.18,6),
 'tailoring':(180,55,7500,12,45000,'job',.035,3),
 'agriculture':(45,31,8000,140,100000,'kg',.12,4),
 'poultry':(7,5,8000,1200,140000,'egg',.10,2),
 'fish':(220,160,9000,25,100000,'kg',.06,3),
 'repair':(250,90,7000,8,50000,'job',.025,3),
 'craft':(300,130,6000,7,40000,'item',.015,2),
 'manufacturing':(25,17,18000,350,200000,'item',.06,2),
 'transport':(300,170,9000,9,200000,'trip',.025,3),
 'services':(80,22,6500,25,60000,'job',.055,3),
 'other':(100,65,9000,25,100000,'unit',.04,3)}
save('sectors.json',{k:dict(price=p,variable_cost=v,fixed_cost=f,daily_capacity=q,starter_cost=s,unit=u,adoption=a,competitors_per_10000=c,estimated=True,source='curated-sector-priors') for k,(p,v,f,q,s,u,a,c) in sectors.items()})
print('Prepared',len(districts),'districts,',len(blocks),'blocks,',len(villages),'panchayats;',len(skipped),'unparsed rows')
