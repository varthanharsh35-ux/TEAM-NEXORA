from pathlib import Path
from contextlib import contextmanager
from datetime import datetime,timezone
import json,sqlite3,uuid,math
from fastapi import HTTPException
from intelligence import resolve_location,classify,retrieve,SECTORS,DATA
from finance import calculate

DB=DATA/'reports.sqlite3'
@contextmanager
def connection():
 c=sqlite3.connect(DB,timeout=15)
 try:
  with c:
   c.execute('CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
   yield c
 finally:c.close()
def save_report(r):
 with connection() as c:c.execute('INSERT OR REPLACE INTO reports VALUES (?,?)',(r['id'],json.dumps(r,ensure_ascii=False)))
def read_report(id):
 with connection() as c:row=c.execute('SELECT body FROM reports WHERE id=?',(id,)).fetchone()
 return json.loads(row[0]) if row else None
def observed_competitors(place, category, radius_km):
 """The competitor count for a report is the mapped count, not a second estimate.

 The report previously computed rivals = population * competitors_per_10000 / 10000
 from a curated constant while the map showed unrelated OSM results, so the two
 disagreed by construction (RULES.md rule 5). Where the location has coordinates
 and an observation is already cached, that measured count is the single source
 of truth. The map is loaded during onboarding before the report is generated,
 so in the real flow the observation is present.
 Where it does not, the estimate is returned but labelled as one -- never silently
 substituted for a measurement.
 """
 lat,lon=place.get('lat'),place.get('lon')
 if lat is None or lon is None:return None
 try:
  from geography import nearby
  result=nearby(lat,lon,category,radius_km=radius_km,cache_only=True)
 except Exception:return None
 if result is None:return None
 competitors=result.get('layers',{}).get('competitors')
 if competitors is None or result.get('completeness')=='unknown':return None
 return {'count':len(competitors),'items':competitors,
         'completeness':result.get('completeness'),
         'completeness_note_key':result.get('completeness_note_key'),
         'observed':result.get('observed'),
         'provenance':result.get('provenance')}

def build_report(data):
 if not data['business'].strip() or not data['location'].strip():raise HTTPException(422,detail='invalid_input')
 loc=resolve_location(data['location'],data.get('district',''))
 if loc['status'] in ['clarify','ambiguous','outside_state']:
  raise HTTPException(422,detail={'error':loc['status'],'candidates':loc['candidates']})
 business=classify(data['business'],data.get('category','auto'));cat=business['category'];s=SECTORS[cat];d=loc['district']
 from planning import starter_budget
 budget=starter_budget(s,d,data.get('facilities',[]))
 cost_based=data.get('funding_mode','legacy')!='legacy'
 scheme=data.get('scheme_id','auto')
 if cost_based and scheme=='auto' and data.get('community')=='obc':scheme='nbcfdc'
 try:f=calculate(data['margin'],data['start_date'],scheme,budget['project_cost'] if cost_based else None)
 except ValueError as e:raise HTTPException(422,detail=str(e))
 p=f['project_cost'];index=d['purchasing_index_estimate']
 population=round(math.pi*data['radius']**2*d['density_estimate']*.35)
 households=round(population/3.8)
 radius=data['radius'] if data['radius'] in (5,10,15) else 15
 measured=observed_competitors(loc.get('place') or {},cat,radius)
 estimated_rivals=round(population*s['competitors_per_10000']/10000)
 rivals=measured['count'] if measured else estimated_rivals
 competitor_source=dict(measured or {'count':estimated_rivals,'items':[],
   'completeness':'unknown','completeness_note_key':'notes.competitors_not_measured',
   'provenance':{'method':'estimated','source':'curated-sector-priors'}})
 block_rivals=round(100000*s['competitors_per_10000']/10000)
 scale=max(.15,min(3,math.sqrt(p/s['starter_cost'])))
 price=round(s['price']*index,2);variable=round(s['variable_cost']*(.95+index*.05),2)
 capacity=round(s['daily_capacity']*26*scale)
 frequency={'dairy':30,'retail':8,'food':12,'agriculture':6,'poultry':30,'fish':4}.get(cat,1)
 demand=round(households*s['adoption']*frequency/(rivals+1))
 units=min(capacity,demand)
 fixed=round(s['fixed_cost']*index*math.sqrt(scale))
 if 'space' in data.get('facilities',[]):fixed=round(fixed*.8)
 revenue=round(units*price,2);variable_total=round(units*variable,2);expenses=round(fixed+variable_total,2)
 wc=round(expenses*1.5+revenue*.25-variable_total*.2,2)
 debt=round(f['quarterly_payment']/3,2)
 operating=round(revenue-expenses,2);net=round(operating-debt,2)
 break_units=math.ceil((fixed+debt)/(price-variable)) if price>variable else None
 projection=[]
 allocated=budget['working_reserve'] if cost_based else round(p*.3,2)
 balance=allocated
 for month in range(1,13):
  ramp=min(1,.55+month*.075);rev=round(revenue*ramp,2);cost=round(fixed+variable_total*ramp,2)
  payment=next((x['payment'] for x in f['schedule'] if x['month']==month),0)
  cash=round(rev-cost-payment,2);balance=round(balance+cash,2)
  projection.append(dict(month=month,revenue=rev,costs=cost,repayment=payment,cash=cash,balance=balance))
 metrics=dict(population=population,population_low=round(population*.65),population_high=round(population*1.35),households=households,competitors=rivals,competitor_source=competitor_source,block_competitors=block_rivals,price=price,price_low=round(price*.9,2),price_high=round(price*1.1,2),variable_unit=variable,fixed_cost=fixed,variable_cost=variable_total,monthly_cost=expenses,revenue=revenue,operating_profit=operating,net_after_debt=net,working_capital=wc,working_allocated=allocated,working_gap=max(0,round(wc-allocated,2)),break_even_units=break_units,units=units,capacity=capacity,starter_cost=round(s['starter_cost']*index),established_cost=round(s['starter_cost']*index*3),unit=s['unit'],downside_profit=round(revenue*.75-fixed-variable_total*.75-debt,2),price_index=index,density=d['density_estimate'],projection=projection)
 retrieved=retrieve(data['business'],d['id'],cat)
 result={'id':uuid.uuid4().hex,'created_at':datetime.now(timezone.utc).isoformat(),'input':data,'location':loc,'business':business,'finance':f,'metrics':metrics,'verdict':'pilot' if net>0 and wc<=allocated and f['funding_gap']==0 and p>=s['starter_cost']*index and not business['uncertain'] else 'caution','retrieval':retrieved,'advice':{},'ai_status':{},'version':2,'sources':['tnrd-villages','tnrd-blocks','district-list','nabard','nsfdc','curated-sector-priors','curated-district-profiles'],'estimated':True}
 required={'dairy':['space','water','power','cold'],'food':['space','water','power'],'manufacturing':['space','three_phase','water','storage'],'retail':['space','storage'],'fish':['water','cold','transport'],'agriculture':['water','storage'],'poultry':['space','water'],'repair':['space','power','equipment'],'tailoring':['space','power','equipment']}.get(cat,['space','power'])
 from schemes import screen
 result['budget']=budget
 result['funding']={'mode':data.get('funding_mode','legacy'),'savings':data['margin'],'used':f['margin'],'remaining':max(0,round(data['margin']-f['margin'],2)),'loan_needed':max(0,round(f['project_cost']-f['margin'],2)),'minimum_contribution':round(f['project_cost']*(.15 if scheme=='nbcfdc' else .1),2),'estimated':True}
 result['scheme_screening']=screen({**data,'project_cost':f['project_cost']})
 result['readiness']={'required':required,'available':data.get('facilities',[]),'missing':[k for k in required if k not in data.get('facilities',[])],'estimated':True}
 checks={'facilities':not result['readiness']['missing'],'funding':f['funding_gap']==0,'cashflow':net>0,'working':wc<=allocated,'evidence':False}
 result['readiness']['checks']=checks
 result['readiness']['score']=sum(checks.values())*2
 if result['readiness']['missing']:result['verdict']='caution'

 # Integrate seasonality
 try:
  from seasonality import monthly_index, seasonality_note_key
  dist_id = d.get('id') if isinstance(d, dict) else str(d)
  curr_month = datetime.now(timezone.utc).month
  result['seasonality'] = monthly_index(cat, dist_id)
  result['seasonality_note_key'] = seasonality_note_key(cat, curr_month)
 except Exception:
  pass

 # Integrate pricing strategy
 try:
  from pricing import strategy as calc_pricing_strategy
  price_band = {'low': metrics['price_low'], 'mid': metrics['price'], 'high': metrics['price_high'], 'unit': s['unit'], 'source': 'Agmarknet / Sector Benchmark', 'date': datetime.now(timezone.utc).date().isoformat()}
  result['pricing_strategy'] = calc_pricing_strategy(
   activity_id=cat,
   demand_score=round(metrics.get('density', 50)),
   competitor_count=rivals,
   competitor_within_1km=min(rivals, 1),
   project_cost=p,
   loan=f['loan'],
   quarterly_payment=f['quarterly_payment'],
   capacity_units_per_month=capacity,
   unit_label=s['unit'],
   sector_price_band=price_band
  )
 except Exception:
  pass

 save_report(result)
 return result
