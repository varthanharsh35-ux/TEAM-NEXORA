import unittest,os,json
from intelligence import resolve_location,classify,retrieve,DISTRICTS,BLOCKS,VILLAGES
from advisory import build_report,read_report
from llm import validate
class Intelligence(unittest.TestCase):
 def test_coverage(self):
  self.assertEqual(len(DISTRICTS),38);self.assertGreaterEqual(len(BLOCKS),380);self.assertGreater(len(VILLAGES),12000)
  
  for district in DISTRICTS:
   for name in district['names'].values():self.assertEqual(resolve_location(name)['district']['id'],district['id'])
  ids={d['id'] for d in DISTRICTS};self.assertTrue(all(v['district'] in ids for v in VILLAGES))
 def test_locations(self):
  for q,d in [('Madurai','Madurai'),('coimbatore','Coimbatore'),('மதுரை','Madurai'),('मदुरै','Madurai'),('Coimbatire','Coimbatore'),('Alanganallur, Madurai','Madurai'),('Imaginary hamlet, Madurai','Madurai')]:
   with self.subTest(q=q):self.assertEqual(resolve_location(q)['district']['id'],d)
  self.assertEqual(resolve_location('Pune, Maharashtra')['status'],'outside_state')
  self.assertIn(resolve_location('Pudur')['status'],['ambiguous','clarify'])
  self.assertEqual(resolve_location('zzxxqq')['status'],'clarify')
 def test_classifier(self):
  for q,c in [('dairy milk','dairy'),('பால் பண்ணை','dairy'),('दूध डेयरी','dairy'),('tailoring blouse stitching','tailoring')]:self.assertEqual(classify(q)['category'],c)
  self.assertTrue(classify('quantum spacetime research')['uncertain'])
 def test_report(self):
  r=build_report(dict(margin=100000,start_date='2026-09-24',location='Alanganallur, Madurai',business='dairy milk',radius=5,language='en'))
  self.assertEqual(r['finance']['loan'],900000);self.assertTrue(r['retrieval']);self.assertEqual(read_report(r['id'])['id'],r['id'])
  self.assertEqual(r['metrics']['monthly_cost'],r['metrics']['fixed_cost']+r['metrics']['variable_cost'])
 def test_json_guard(self):
  with self.assertRaises(Exception):validate('{"market":"bad"}','en')
  o={k:'This is English advice.' for k in ['market','opportunity','strengths','weaknesses','threats','competition','pricing','steps']}
  with self.assertRaises(Exception):validate(json.dumps(o),'ta')
if __name__=='__main__':unittest.main()
