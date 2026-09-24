import unittest
from unittest.mock import patch,MagicMock
import main
from fastapi.testclient import TestClient
from main import app
class API(unittest.TestCase):
 def test_contract(self):
  c=TestClient(app)
  self.assertEqual(c.get('/api/health').status_code,200)
  self.assertEqual(c.post('/api/finance',json={'margin':100000}).json()['loan'],900000)
  for v in [0,-1,'bad',None,True,.001]:self.assertEqual(c.post('/api/finance',json={'margin':v}).status_code,422)
  self.assertEqual(c.post('/api/finance',json={'margin':10000,'start_date':'bad'}).status_code,422)
  self.assertEqual(c.post('/api/finance',json={'margin':10000,'start_date':'9999-01-01'}).status_code,422)
 def test_report_failures(self):
  c=TestClient(app);base={'margin':100000,'location':'Madurai','business':'dairy'}
  self.assertEqual(c.post('/api/reports',json={**base,'business':'   '}).status_code,422)
  self.assertEqual(c.post('/api/reports',json={**base,'location':'Pune Maharashtra'}).json()['detail']['error'],'outside_state')
  self.assertEqual(c.post('/api/reports',json={**base,'location':'unknown village'}).json()['detail']['error'],'clarify')
  self.assertEqual(c.get('/api/reports/not-found').status_code,404)
  self.assertEqual(c.get('/api/geocode?lat=20&lon=78').status_code,422)
 def test_map_provider_failure_and_cache(self):
  c=TestClient(app);main.GEOCODE_CACHE.clear();main.GEOCODE_LAST=0
  with patch('httpx.Client',side_effect=RuntimeError('offline')):
   self.assertEqual(c.get('/api/geocode?lat=9.9&lon=78.1').status_code,503)
  main.GEOCODE_LAST=0
  client=MagicMock();client.__enter__.return_value=client
  client.get.return_value.json.return_value={'address':{'state':'Tamil Nadu'},'display_name':'Alanganallur, Madurai, Tamil Nadu'}
  with patch('httpx.Client',return_value=client):
   result=c.get('/api/geocode?lat=10&lon=78').json()
   self.assertEqual(result['district'],'Madurai')
   self.assertEqual(c.get('/api/geocode?lat=10&lon=78').json(),result)
   self.assertEqual(client.get.call_count,1)
  main.GEOCODE_CACHE.clear();main.GEOCODE_LAST=0
if __name__=='__main__':unittest.main()
