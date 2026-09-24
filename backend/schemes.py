from pathlib import Path
import json
CATALOG=json.loads((Path(__file__).resolve().parents[1]/'data/scheme_catalog.json').read_text())
def screen(data):
 result=[]
 for item in CATALOG['schemes']:
  reasons=[];missing=[];project=data.get('project_cost') or round(data['margin']/(1-item['share']),2)
  if data.get('funding_mode','legacy')!='legacy' and not data.get('project_cost'):
   from intelligence import SECTORS,resolve_location
   from planning import starter_budget
   loc=resolve_location(data.get('location',''),data.get('district',''))
   if loc.get('district'):project=starter_budget(SECTORS.get(data.get('category'),SECTORS['other']),loc['district'],data.get('facilities',[]))['project_cost']
  if data.get('community','unspecified')=='unspecified':missing.append('community')
  elif data['community']!=item['community']:reasons.append('community_mismatch')
  if data.get('household_income') is None:missing.append('household_income')
  elif data['household_income']>item['income_limit']:reasons.append('income_above')
  if (item['minimum_project'] and project<=item['minimum_project']) or (item['maximum_project'] and project>item['maximum_project']):reasons.append('project_mismatch')
  result.append({**item,'project_cost':project,'status':'not_eligible' if reasons else 'need_details' if missing else 'potential','reasons':reasons,'missing':missing})
 return {'schemes':result,'checked':CATALOG['checked']}
