"""Regressions and integration tests for newly wired FastAPI endpoints."""

import unittest
from fastapi.testclient import TestClient
from main import app


class NewFeaturesAPITest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_seasonality_endpoint(self):
        res = self.client.get('/api/seasonality/food.cafe?district=chennai')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['activity_id'], 'food.cafe')
        self.assertEqual(data['district'], 'chennai')
        self.assertIsNotNone(data['climate'])
        self.assertEqual(len(data['monthly_index']), 12)
        # Check Apr/May vacation suppression
        self.assertEqual(data['monthly_index'][3]['index'], 0.6)

    def test_seasonality_no_district(self):
        res = self.client.get('/api/seasonality/retail.grocery')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsNone(data['climate'])
        self.assertEqual(len(data['monthly_index']), 12)
        # Check Jan Pongal boost
        self.assertEqual(data['monthly_index'][0]['index'], 1.3)

    def test_pricing_strategy_endpoint(self):
        payload = {
            "activity_id": "dairy.milk_collection",
            "demand_score": 75,
            "competitor_count": 1,
            "competitor_within_1km": 0,
            "project_cost": 100000.0,
            "loan": 80000.0,
            "quarterly_payment": 6000.0,
            "capacity_units_per_month": 1000.0,
            "unit_label": "litre",
            "sector_price_band": {
                "low": 40.0,
                "mid": 50.0,
                "high": 60.0,
                "unit": "litre",
                "source": "Agmarknet",
                "date": "2026-09-24"
            }
        }
        res = self.client.post('/api/pricing/strategy', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['recommended'], 'premium')
        self.assertEqual(len(data['positions']), 3)
        self.assertIn('sensitivity', data)

    def test_pricing_strategy_validation_error(self):
        # Negative capacity should trigger 422
        bad_payload = {
            "activity_id": "dairy.milk_collection",
            "demand_score": 150,  # invalid > 100
            "competitor_count": 1,
            "competitor_within_1km": 0,
            "project_cost": 100000.0,
            "loan": 80000.0,
            "quarterly_payment": 6000.0,
            "capacity_units_per_month": -10.0,
            "unit_label": "litre",
            "sector_price_band": {}
        }
        res = self.client.post('/api/pricing/strategy', json=bad_payload)
        self.assertEqual(res.status_code, 422)

    def test_better_activities_endpoint(self):
        payload = {
            "location_id": "loc_1",
            "lat": 11.0,
            "lon": 78.0,
            "chosen_activity_id": "agriculture.paddy",
            "chosen_demand_score": 40,
            "margin": 50000.0,
            "radius_km": 10.0,
            "top_n": 3
        }
        res = self.client.post('/api/alternatives/activities', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('alternatives', data)
        self.assertEqual(data['chosen_score'], 40)
        self.assertIn('provenance', data)

    def test_better_locations_endpoint(self):
        payload = {
            "chosen_activity_id": "food.cafe",
            "chosen_lat": 12.77,
            "chosen_lon": 79.83,
            "chosen_demand_score": 40,
            "radius_km": 25.0,
            "top_n": 3
        }
        res = self.client.post('/api/alternatives/locations', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('better_locations', data)

    def test_tracker_crud_cycle(self):
        user_id = 'test_api_tracker_user'
        entry_payload = {
            "date": "2026-03-10",
            "kind": "income",
            "category": "sales",
            "amount": 4500.0,
            "note": "API test sale"
        }
        # 1. Add entry
        post_res = self.client.post(f'/api/tracker/entries?user_id={user_id}', json=entry_payload)
        self.assertEqual(post_res.status_code, 200)
        entry = post_res.json()
        self.assertEqual(entry['amount'], 4500.0)
        entry_id = entry['id']

        # 2. Get summary
        sum_res = self.client.get(f'/api/tracker/summary?user_id={user_id}')
        self.assertEqual(sum_res.status_code, 200)
        sum_data = sum_res.json()
        self.assertGreaterEqual(sum_data['totals']['income'], 4500.0)

        # 3. Delete entry
        del_res = self.client.delete(f'/api/tracker/entries/{entry_id}?user_id={user_id}')
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(del_res.json()['status'], 'deleted')

        # 4. Deleting again returns 404
        del_res_again = self.client.delete(f'/api/tracker/entries/{entry_id}?user_id={user_id}')
        self.assertEqual(del_res_again.status_code, 404)

    def test_debt_portfolio_cycle(self):
        user_id = 'test_api_debt_user'
        loan_payload = {
            "lender": "Indian Overseas Bank",
            "facility_type": "term_loan",
            "status": "active",
            "principal": 50000.0,
            "annual_rate": 10.0,
            "tenure_months": 12,
            "disbursement_date": "2026-01-15",
            "grace_months": 0
        }
        # 1. Add loan
        post_res = self.client.post(f'/api/debt/loans?user_id={user_id}', json=loan_payload)
        self.assertEqual(post_res.status_code, 200)
        loan = post_res.json()
        loan_id = loan['id']
        self.assertGreater(loan['emi'], 0)

        # 2. List loans
        list_res = self.client.get(f'/api/debt/loans?user_id={user_id}')
        self.assertEqual(list_res.status_code, 200)
        data = list_res.json()
        self.assertGreaterEqual(len(data['loans']), 1)
        self.assertGreater(data['portfolio_totals']['monthly_emi_obligation'], 0)

        # 3. Close loan
        close_res = self.client.post(f'/api/debt/loans/{loan_id}/close?user_id={user_id}')
        self.assertEqual(close_res.status_code, 200)
        self.assertEqual(close_res.json()['status'], 'closed')

    def test_freshness_endpoint(self):
        res = self.client.get('/api/freshness')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('datasets', data)
        self.assertIn('as_of', data)


if __name__ == '__main__':
    unittest.main()
