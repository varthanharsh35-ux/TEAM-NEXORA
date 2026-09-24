"""Task 1.2 regressions. Every Overpass response is stubbed; no network calls."""
import copy
import json
import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient

import geography
from main import app


FIXTURE = Path(__file__).resolve().parents[1] / 'tests/fixtures/sarvanampatti_pois_osm.json'


class GeographyLayersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(FIXTURE.read_text(encoding='utf-8'))
        cls.lat = 11.0783323
        cls.lon = 77.0038210

    def setUp(self):
        self.store = {}
        self.client = MagicMock()
        self.client.__enter__.return_value = self.client
        self.client.get.return_value.json.return_value = copy.deepcopy(self.raw)
        self.client_patch = patch('geography.httpx.Client', return_value=self.client)
        self.cache_patch = patch('geography.cached', side_effect=self.cache)
        self.last_patch = patch('geography.LAST', 0)
        self.client_patch.start()
        self.cache_patch.start()
        self.last_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.addCleanup(self.cache_patch.stop)
        self.addCleanup(self.last_patch.stop)

    def cache(self, key, value=None):
        if value is not None:
            self.store[key] = (copy.deepcopy(value), geography.time.time())
            return value
        return copy.deepcopy(self.store.get(key))

    def fetch(self, activity='poultry.broiler', radius=15):
        geography.LAST = 0
        return geography.nearby(self.lat, self.lon, activity, radius_km=radius)

    def test_real_fixture_blood_banks_never_enter_any_layer(self):
        blood_ids = {
            f"{item['type']}/{item['id']}"
            for item in self.raw['elements']
            if item.get('tags', {}).get('amenity') == 'blood_bank'
        }
        self.assertEqual(len(blood_ids), 14, 'Fixture must contain the reported bad records')
        result = self.fetch()
        for name, points in result['layers'].items():
            self.assertFalse(blood_ids.intersection(point['id'] for point in points), name)
        self.assertGreater(len(result['layers']['competitors']), 0)
        self.assertTrue(all(point['match'] == 'adjacent' for point in result['layers']['competitors']))

    def test_banks_and_post_offices_are_only_amenities(self):
        result = self.fetch(radius=15)
        amenity_ids = {
            f"{item['type']}/{item['id']}"
            for item in self.raw['elements']
            if item.get('tags', {}).get('amenity') in ('bank', 'post_office')
        }
        competitor_ids = {point['id'] for point in result['layers']['competitors']}
        returned_amenities = {point['id'] for point in result['layers']['amenities']}
        self.assertTrue(returned_amenities)
        self.assertTrue(returned_amenities <= amenity_ids)
        self.assertFalse(competitor_ids & amenity_ids)
        self.assertEqual(result['layers']['drivers'], [])

    def test_radius_changes_query_counts_and_cache_key(self):
        five = self.fetch(radius=5)
        five_query = self.client.get.call_args.kwargs['params']['data']
        ten = self.fetch(radius=10)
        ten_query = self.client.get.call_args.kwargs['params']['data']
        self.assertIn('(around:5000,', five_query)
        self.assertIn('(around:10000,', ten_query)
        self.assertNotIn('(around:15000,', five_query)
        self.assertLess(len(five['layers']['competitors']), len(ten['layers']['competitors']))
        self.assertLess(len(five['layers']['amenities']), len(ten['layers']['amenities']))
        self.assertTrue(all(point['distance_m'] <= 5000 for point in five['layers']['competitors']))
        self.assertTrue(all(point['distance_m'] <= 10000 for point in ten['layers']['competitors']))
        self.assertEqual(len(self.store), 2)
        self.assertEqual(self.fetch(radius=5), five)
        self.assertEqual(self.client.get.call_count, 2, 'Radius-specific cache must be reused')

    def test_every_regex_is_anchored(self):
        selectors = [
            selector
            for activity in geography.TAGS.values()
            for group in ('direct', 'adjacent')
            for selector in activity[group]
        ]
        self.fetch()
        selectors.append(self.client.get.call_args.kwargs['params']['data'])
        for selector in selectors:
            for expression in re.findall(r'~"([^"]+)"', selector):
                for alternative in expression.split('|'):
                    self.assertTrue(alternative.startswith('^'), expression)
                    self.assertTrue(alternative.endswith('$'), expression)

    def test_all_required_poultry_selectors_and_adjacent_matches(self):
        tags = [
            {'shop': 'butcher'},
            {'landuse': 'farmyard', 'poultry': 'yes'},
            {'landuse': 'farmyard', 'farmyard': 'poultry'},
            {'man_made': 'poultry'},
            {'shop': 'supermarket'},
            {'shop': 'convenience'},
            {'amenity': 'marketplace'},
            {'amenity': 'blood_bank', 'shop': 'butcher'},
            {'shop': 'not_supermarket'},
            {'man_made': 'poultry_equipment'},
            {'landuse': 'farmyard', 'poultry': 'no'},
            {'landuse': 'farmyard'},
            {'amenity': 'bank', 'shop': 'butcher'},
        ]
        elements = [
            {'type': 'node', 'id': index, 'lat': self.lat, 'lon': self.lon, 'tags': tag}
            for index, tag in enumerate(tags)
        ]
        elements.append(copy.deepcopy(elements[0]))
        self.client.get.return_value.json.return_value = {'elements': elements}
        result = self.fetch()
        matches = {point['id']: point['match'] for point in result['layers']['competitors']}
        self.assertEqual(matches, {
            **{f'node/{index}': 'direct' for index in range(4)},
            **{f'node/{index}': 'adjacent' for index in range(4, 7)},
        })
        self.assertEqual([point['id'] for point in result['layers']['amenities']], ['node/12'])
        query = self.client.get.call_args.kwargs['params']['data']
        for group in geography.TAGS['poultry.broiler'].values():
            for selector in group:
                self.assertIn('nwr' + selector, query)

    def test_legacy_mixed_cache_cannot_contaminate_layers(self):
        key = f'nearby:{self.lat:.4f}:{self.lon:.4f}:poultry'
        self.store[key] = ({'points': [{'id': 'bad', 'kind': 'competitor'}]}, geography.time.time())
        result = self.fetch(activity='poultry')
        self.client.get.assert_called_once()
        self.assertNotIn('points', result)
        self.assertFalse(any(point['id'] == 'bad' for point in result['layers']['competitors']))

    def test_contract_and_partial_coverage_even_for_empty_response(self):
        self.client.get.return_value.json.return_value = {'elements': []}
        result = self.fetch()
        self.assertEqual(set(result['layers']), {'competitors', 'drivers', 'amenities'})
        self.assertEqual(result['centre'], {'lat': self.lat, 'lon': self.lon})
        self.assertEqual(result['radius_km'], 15)
        self.assertEqual(result['completeness'], 'partial')
        self.assertEqual(result['completeness_note_key'], 'notes.osm_partial')
        self.assertEqual(result['freshness']['status'], 'fresh')
        self.assertTrue(result['provenance']['source_url'])

    def test_outage_and_malformed_response_are_explicit_failures(self):
        for raw in ({}, {'elements': None}, {'elements': [], 'remark': 'runtime timeout'}):
            with self.subTest(raw=raw):
                self.client.get.return_value.json.return_value = raw
                with self.assertRaises(HTTPException) as error:
                    self.fetch()
                self.assertEqual(error.exception.detail['status'], 'unresolved')
                self.assertEqual(error.exception.detail['error'], 'source_unavailable')
        self.client.get.side_effect = httpx.ConnectError('offline')
        with self.assertRaises(HTTPException) as error:
            self.fetch()
        self.assertEqual(error.exception.status_code, 503)

    def test_stale_fallback_retains_observation_date_and_labels_staleness(self):
        original = self.fetch()
        key = next(iter(self.store))
        self.store[key] = (self.store[key][0], geography.time.time() - 8 * 86400)
        self.client.get.side_effect = httpx.ConnectError('offline')
        result = self.fetch()
        self.assertEqual(result['layers'], original['layers'])
        self.assertEqual(result['observed'], original['observed'])
        self.assertEqual(result['provenance'], original['provenance'])
        self.assertEqual(result['freshness']['status'], 'stale')

    def test_invalid_radius_and_unknown_activity_never_call_http(self):
        for radius in (0, -5, 7, float('nan'), float('inf')):
            with self.subTest(radius=radius), self.assertRaises(HTTPException):
                self.fetch(radius=radius)
        with self.assertRaises(HTTPException):
            self.fetch(activity='unknown.activity')
        self.client.get.assert_not_called()

    def test_route_passes_activity_and_radius(self):
        client = TestClient(app)
        params = {'lat': self.lat, 'lon': self.lon, 'activity_id': 'poultry.broiler', 'radius_km': 5}
        response = client.get('/api/map/nearby', params=params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['radius_km'], 5)
        self.assertIn('(around:5000,', self.client.get.call_args.kwargs['params']['data'])

    def test_location_id_requires_real_coordinates(self):
        client = TestClient(app)
        params = {'location_id': 'test:locality', 'activity_id': 'poultry.broiler', 'radius_km': 10}
        registry = [{'id': 'test:locality', 'lat': self.lat, 'lon': self.lon}]
        with patch('main.Path.read_text', return_value=json.dumps(registry)):
            response = client.get('/api/map/nearby', params=params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['radius_km'], 10)
        self.client.reset_mock()
        with patch('main.Path.read_text', return_value=json.dumps([{'id': 'test:locality'}])):
            response = client.get('/api/map/nearby', params=params)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail']['error'], 'location_unresolved')
        self.client.get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
