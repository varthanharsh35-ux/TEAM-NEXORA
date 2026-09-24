import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
import accounts
class Accounts(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.dbpatch=patch.object(accounts,'DB',Path(self.temp.name)/'accounts.db');self.dbpatch.start();accounts.ATTEMPTS.clear();self.c=TestClient(app);self.login={'email':'one@example.test','password':'Strong-local-password-2026'}
 def tearDown(self):self.dbpatch.stop();self.temp.cleanup()
 def test_registration_private_storage_logout(self):
  self.assertEqual(self.c.get('/api/account/workspace').status_code,401)
  r=self.c.post('/api/account/register',json=self.login);self.assertEqual(r.status_code,200);self.assertIn('httponly',r.headers['set-cookie'].lower())
  self.assertEqual(self.c.post('/api/account/workspace',json={'profile':{'community':'sc'}}).status_code,200)
  other=TestClient(app);other.post('/api/account/register',json={**self.login,'email':'two@example.test'})
  self.assertEqual(other.get('/api/account/workspace').json(),{})
  self.assertEqual(self.c.get('/api/account/workspace').json()['profile']['community'],'sc')
  self.c.post('/api/account/logout');self.assertEqual(self.c.get('/api/account/workspace').status_code,401)
  self.assertEqual(self.c.post('/api/account/login',json=self.login).status_code,200)
 def test_recovery_revokes_sessions(self):
  code=self.c.post('/api/account/register',json=self.login).json()['recovery'];other=TestClient(app)
  reset=other.post('/api/account/reset',json={**self.login,'password':'New-long-password-2026','recovery':code})
  self.assertEqual(reset.status_code,200);self.assertEqual(self.c.get('/api/account/workspace').status_code,401)
  self.assertEqual(other.post('/api/account/login',json=self.login).status_code,401)
  self.assertEqual(other.post('/api/account/login',json={**self.login,'password':'New-long-password-2026'}).status_code,200)
  self.assertEqual(other.post('/api/account/reset',json={**self.login,'recovery':code}).status_code,401)
 def test_origin_and_validation(self):
  self.assertEqual(self.c.post('/api/account/register',json=self.login,headers={'Origin':'https://untrusted.example'}).status_code,403)
  self.assertEqual(self.c.post('/api/account/register',json={**self.login,'password':'short'}).status_code,422)
  self.assertEqual(self.c.post('/api/account/register',json={**self.login,'email':'not-an-email'}).status_code,422)
  self.c.post('/api/account/register',json=self.login)
  with accounts.db() as c:
   row=c.execute('SELECT * FROM users').fetchone();self.assertNotEqual(row['password'],self.login['password']);self.assertEqual(len(row['salt']),32)
if __name__=='__main__':unittest.main()
