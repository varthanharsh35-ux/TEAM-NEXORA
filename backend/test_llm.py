import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
import httpx
import llm

class LLMTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);(root/'data').mkdir()
  self.root=patch.object(llm,'ROOT',root);self.root.start()
  self.env=patch.dict(os.environ,{'LLM_BASE_URL':'https://invalid.example/v1','LLM_MODEL':'test','LOCAL_LLM':'0'});self.env.start()
  self.report={'input':{'business':'dairy'},'location':{'district':{'id':'Madurai'}},'business':{'category':'dairy'},'verdict':'caution','retrieval':[]}
  self.valid={k:'Confirm local demand before buying equipment.' for k in llm.Advice.model_fields}
 def tearDown(self):
  self.root.stop();self.env.stop();self.temp.cleanup()
 def test_api_outage_is_graceful(self):
  with patch.object(llm.httpx,'Client',side_effect=httpx.ConnectError('offline')):
   advice,provider,failures=llm.generate(self.report,'en')
  self.assertIsNone(advice);self.assertEqual(provider,'curated');self.assertIn('api_unavailable_or_invalid',failures)
 def test_bad_api_output_is_rejected(self):
  for output in ['not json',json.dumps({**self.valid,'pricing':'Charge 100 rupees.'}),json.dumps(self.valid)]:
   with self.subTest(output=output):
    client=MagicMock();client.__enter__.return_value=client
    client.post.return_value.json.return_value={'choices':[{'message':{'content':output}}]}
    with patch.object(llm.httpx,'Client',return_value=client):
     advice,provider,_=llm.generate(self.report,'ta')
    self.assertIsNone(advice);self.assertEqual(provider,'curated')
 def test_valid_advice_is_cached_and_schema_checked(self):
  obj={**self.valid,'steps':['Ask local customers first.','Compare supplier reliability.']}
  client=MagicMock();client.__enter__.return_value=client
  client.post.return_value.json.return_value={'choices':[{'message':{'content':json.dumps(obj)}}]}
  with patch.object(llm.httpx,'Client',return_value=client):
   advice,provider,_=llm.generate(self.report,'en')
  self.assertEqual(provider,'api');self.assertIsInstance(advice['steps'],str)
  with patch.object(llm.httpx,'Client',side_effect=AssertionError('Cache should avoid request')):
   again,provider,failures=llm.generate(self.report,'en')
  self.assertEqual(again,advice);self.assertEqual(failures,['cached'])

if __name__=='__main__':unittest.main()
