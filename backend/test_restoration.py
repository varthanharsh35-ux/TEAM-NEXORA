import unittest
from fastapi.testclient import TestClient
from main import app
from finance import calculate
from schemes import screen
class Restoration(unittest.TestCase):
 def test_nbcfdc_terms(self):
  small=calculate(15000,'2026-01-01','nbcfdc')
  self.assertEqual((small['project_cost'],small['loan'],small['annual_rate'],small['tenure_months'],small['moratorium_months']),(100000,85000,7,48,3))
  large=calculate(150000,'2026-01-01','nbcfdc')
  self.assertEqual((large['loan'],large['annual_rate'],large['tenure_months']),(850000,8,84))
  self.assertEqual(large['schedule'][-1]['balance'],0)
  self.assertEqual(large['schedule'][0]['payment'],0)
  capped=calculate(500000,'2026-01-01','nbcfdc');self.assertEqual(capped['loan'],1500000);self.assertGreater(capped['funding_gap'],0)
 def test_screening_is_not_approval(self):
  base={'margin':100000,'community':'sc','household_income':400000}
  result={r['id']:r for r in screen(base)['schemes']}
  self.assertEqual(result['term']['status'],'potential');self.assertEqual(result['micro']['status'],'not_eligible');self.assertEqual(result['nbcfdc']['status'],'not_eligible')
  self.assertEqual(screen({'margin':100000})['schemes'][1]['status'],'need_details')
  self.assertEqual(screen({**base,'household_income':500001})['schemes'][1]['status'],'not_eligible')
 def test_guided_profile_contract(self):
  c=TestClient(app);base={'location':'Sarvanampatti, Coimbatore','business':'tailoring','category':'tailoring','margin':150000,'scheme_id':'nbcfdc','community':'obc','gender':'female','age':29,'household_income':200000,'facilities':['space','power','equipment']}
  r=c.post('/api/reports',json=base);self.assertEqual(r.status_code,200);r=r.json()
  self.assertEqual(r['finance']['scheme'],'nbcfdc');self.assertEqual(r['finance']['loan'],850000);self.assertEqual(r['readiness']['missing'],[])
  self.assertEqual(c.post('/api/reports',json={**base,'facilities':['invented']}).status_code,422)
  self.assertEqual(c.post('/api/reports',json={**base,'age':-1}).status_code,422)
  self.assertEqual(c.post('/api/reports',json={**base,'scheme_id':'micro'}).status_code,422)
if __name__=='__main__':unittest.main()
