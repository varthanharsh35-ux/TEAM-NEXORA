"""Transparent starter-budget assumptions. Replace allowances with supplier quotes."""
from finance import money
def starter_budget(sector,district,facilities):
 base=money(sector['starter_cost']*district['purchasing_index_estimate'])
 rows=[]
 for key,part,facility in [('tools',.55,'equipment'),('premises',.20,'space'),('stock',.15,None),('setup',.10,None)]:
  gross=money(base*money(part));owned=facility in facilities if facility else False
  # Equipment ownership is not proof that all required assets are suitable.
  rows.append({'key':key,'amount':float(money(gross*money(.5))) if owned and key=='tools' else 0.0 if owned else float(gross),'provided':owned,'estimated':True})
 reserve=money(sector['fixed_cost']*district['purchasing_index_estimate']*1.5)
 rows.append({'key':'reserve','amount':float(reserve),'provided':False,'estimated':True})
 return {'items':rows,'project_cost':float(sum(money(r['amount']) for r in rows)),'working_reserve':float(reserve),'estimated':True,'source':'curated-sector-priors'}
