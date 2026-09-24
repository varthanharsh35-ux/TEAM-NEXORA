import unittest
from fastapi.testclient import TestClient
from main import app
from finance import calculate
from pathlib import Path
FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
class Basics(unittest.TestCase):
 def test_funding_paths(self):
  c=TestClient(app);base={'location':'Sarvanampatti, Coimbatore','category':'dairy','business':'dairy','funding_mode':'savings','radius':15}
  funded=c.post('/api/reports',json={**base,'margin':1000000}).json()
  self.assertEqual(funded['finance']['scheme'],'self_funded');self.assertEqual(funded['finance']['loan'],0)
  self.assertEqual(funded['finance']['schedule'],[])
  mixed=c.post('/api/reports',json={**base,'margin':100000}).json()
  f=mixed['finance'];self.assertEqual(f['loan']+f['margin']+f['funding_gap'],f['project_cost'])
  self.assertEqual(f['schedule'][-1]['balance'],0)
  zero=c.post('/api/reports',json={**base,'margin':0,'funding_mode':'loan'}).json()
  self.assertGreater(zero['finance']['funding_gap'],0)
  self.assertEqual(c.post('/api/finance',json={'margin':0}).status_code,422)
  self.assertEqual(c.post('/api/reports',json={**base,'margin':-1}).status_code,422)
  owned=c.post('/api/reports',json={**base,'margin':100000,'facilities':['space','equipment']}).json()
  self.assertLess(owned['budget']['project_cost'],mixed['budget']['project_cost'])
 def test_cost_based_cap(self):
  r=calculate(14000,'2026-01-01','micro',140000)
  self.assertEqual(r['loan'],125000);self.assertEqual(r['funding_gap'],1000)
  self.assertEqual(calculate(100000,'2026-01-01')['loan'],900000)
 def test_locality_search_uses_general_path(self):
  # Regression guard for Task 0.3: search() must resolve any locality through the
  # ordinary geocoder path. It previously short-circuited on a hardcoded list of
  # spellings and returned a canned file, so exactly one place in the state worked.
  import geography, json
  raw = json.loads((FIXTURES / 'sarvanampatti_locality_osm.json').read_text(encoding='utf-8'))
  calls = []

  class FakeResponse:
   def raise_for_status(self): pass
   def json(self): return raw

  class FakeClient:
   def __init__(self, **kw): pass
   def __enter__(self): return self
   def __exit__(self, *a): return False
   def get(self, url, params=None, headers=None):
    calls.append(params['q'])
    return FakeResponse()

  original_client, original_cached = geography.httpx.Client, geography.cached
  geography.httpx.Client = FakeClient
  geography.cached = lambda key, value=None: value
  try:
   result = geography.search('Sarvanampatti, Coimbatore')
  finally:
   geography.httpx.Client, geography.cached = original_client, original_cached

  self.assertEqual(len(calls), 1, 'geocoder must actually be called, not short-circuited')
  item = result['items'][0]
  self.assertAlmostEqual(item['lat'], 11.0783323)
  self.assertEqual(item['district'], 'Coimbatore')

 def test_no_hardcoded_place_names(self):
  # RULES.md rule 3: no branch may test for a specific place name.
  import pathlib as _pl
  backend = _pl(__file__).parent if False else _pl.Path(__file__).resolve().parent
  offenders = []
  for path in backend.glob('*.py'):
   if path.name.startswith('test_'): continue
   text = path.read_text(encoding='utf-8').lower()
   for name in ['sarvanampatti', 'saravanampatti', 'lakkapuram', 'coimbatore']:
    if name in text: offenders.append(f'{path.name}: {name}')
  self.assertEqual(offenders, [], f'hardcoded place names found: {offenders}')

 def test_actual_loan(self):
  c=TestClient(app);base={'principal':120000,'rate':0,'tenure':12,'grace':0,'start_date':'2026-01-01'}
  r=c.post('/api/loans/schedule',json=base).json()
  self.assertEqual(r['quarterly_payment'],30000);self.assertEqual(r['total_interest'],0);self.assertEqual(r['schedule'][-1]['balance'],0)
  r=c.post('/api/loans/schedule',json={**base,'rate':8,'grace':3}).json()
  self.assertEqual(r['schedule'][0]['payment'],0);self.assertEqual(r['schedule'][-1]['balance'],0)
  self.assertEqual(c.post('/api/loans/schedule',json={**base,'grace':12}).status_code,422)
  self.assertEqual(c.post('/api/loans/schedule',json={**base,'tenure':10}).status_code,422)
if __name__=='__main__':unittest.main()
