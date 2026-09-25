"""Production storage and reverse-proxy account regression checks."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
import accounts
from main import app
from storage import database_path


class DeploymentTests(unittest.TestCase):
    def test_production_records_are_scoped_to_the_session(self):
        import advisory
        import tracker
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(accounts, 'DB', Path(temp) / 'accounts.sqlite3'), patch.object(advisory, 'DB', Path(temp) / 'reports.sqlite3'), patch.object(tracker, 'DB_PATH', Path(temp) / 'tracker.sqlite3'):
                with patch.dict(os.environ, {'APP_ENV': 'production', 'ALLOWED_ORIGINS': ''}):
                    accounts.ATTEMPTS.clear()
                    with TestClient(app, base_url='https://backend.example') as first, TestClient(app, base_url='https://backend.example') as second, TestClient(app, base_url='https://backend.example') as guest:
                        for client, email in [(first, 'first@example.test'), (second, 'second@example.test')]:
                            response = client.post('/api/account/register', json={'email': email, 'password': 'Deployment-test-password'})
                            self.assertEqual(response.status_code, 200)
                        payload = {'location': 'Madurai', 'business': 'dairy', 'category': 'dairy', 'margin': 100000}
                        report = first.post('/api/reports', json=payload)
                        self.assertEqual(report.status_code, 200, report.text)
                        report_id = report.json()['id']
                        self.assertEqual(first.get(f'/api/reports/{report_id}').status_code, 200)
                        self.assertEqual(second.get(f'/api/reports/{report_id}').status_code, 404)
                        self.assertEqual(guest.get(f'/api/reports/{report_id}').status_code, 401)
                        self.assertEqual(guest.post('/api/reports', json=payload).status_code, 401)
                        entry = {'date': '2026-09-25', 'kind': 'income', 'category': 'sales', 'amount': 123}
                        self.assertEqual(first.post('/api/tracker/entries?user_id=forged', json=entry).status_code, 200)
                        own = first.get('/api/tracker/summary?user_id=forged')
                        self.assertEqual(own.json()['totals']['income'], 123)
                        self.assertEqual(own.headers['cache-control'], 'no-store')
                        self.assertEqual(second.get('/api/tracker/summary?user_id=forged').json()['totals']['income'], 0)
                        self.assertEqual(guest.get('/api/tracker/summary').status_code, 401)
                        self.assertEqual(guest.get('/api/statements/batches').status_code, 401)
                        self.assertEqual(guest.get('/api/debt/loans').status_code, 401)

    def test_storage_creates_persistent_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'volume' / 'databases'
            with patch.dict(os.environ, {'DATA_DIR': str(target)}):
                result = database_path('reports.sqlite3')
            self.assertEqual(result, target / 'reports.sqlite3')
            self.assertTrue(target.is_dir())

    def test_development_storage_default(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {'DATA_DIR': ''}):
                result = database_path('reports.sqlite3', Path(temp))
            self.assertEqual(result, Path(temp) / 'data' / 'reports.sqlite3')

    def test_proxy_login_cookie_and_workspace_persistence(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(accounts, 'DB', Path(temp) / 'accounts.sqlite3'):
            with patch.dict(os.environ, {'APP_ENV': 'production', 'ALLOWED_ORIGINS': 'https://frontend.example'}):
                accounts.ATTEMPTS.clear()
                with TestClient(app, base_url='https://backend.example') as client:
                    headers = {'Origin': 'https://frontend.example'}
                    credentials = {'email': 'deploy@example.test', 'password': 'Deployment-test-password'}
                    response = client.post('/api/account/register', json=credentials, headers=headers)
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertIn('Secure', response.headers['set-cookie'])
                    state = {'profile': {'business_name': 'Persistent test'}}
                    self.assertEqual(client.post('/api/account/workspace', json=state, headers=headers).status_code, 200)
                    client.post('/api/account/logout', headers=headers)
                with TestClient(app, base_url='https://backend.example') as client:
                    self.assertEqual(client.post('/api/account/login', json=credentials, headers=headers).status_code, 200)
                    self.assertEqual(client.get('/api/account/workspace').json()['profile'], state['profile'])
                    for origin in ['https://untrusted.example', 'http://localhost:5173']:
                        response = client.post('/api/account/workspace', json=state, headers={'Origin': origin})
                        self.assertEqual(response.status_code, 403)
