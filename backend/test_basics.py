import unittest
from fastapi.testclient import TestClient
from main import app
from finance import calculate
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
 def test_cached_locality(self):
  c=TestClient(app);r=c.get('/api/map/search',params={'q':'Sarvanampatti, Coimbatore'}).json()['items'][0]
  self.assertAlmostEqual(r['lat'],11.0783323);self.assertEqual(r['district'],'Coimbatore')
 def test_actual_loan(self):
  c=TestClient(app);base={'principal':120000,'rate':0,'tenure':12,'grace':0,'start_date':'2026-01-01'}
  r=c.post('/api/loans/schedule',json=base).json()
  self.assertEqual(r['quarterly_payment'],30000);self.assertEqual(r['total_interest'],0);self.assertEqual(r['schedule'][-1]['balance'],0)
  r=c.post('/api/loans/schedule',json={**base,'rate':8,'grace':3}).json()
  self.assertEqual(r['schedule'][0]['payment'],0);self.assertEqual(r['schedule'][-1]['balance'],0)
  self.assertEqual(c.post('/api/loans/schedule',json={**base,'grace':12}).status_code,422)
  self.assertEqual(c.post('/api/loans/schedule',json={**base,'tenure':10}).status_code,422)
if __name__=='__main__':unittest.main()
