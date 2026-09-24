"""Task 1.3: the report's competitor count is the mapped count, never a parallel estimate."""
import unittest
from unittest.mock import patch

import advisory


class CompetitorSource(unittest.TestCase):
    place = {'name': 'Somewhere', 'district': 'Erode', 'lat': 11.3, 'lon': 77.7}

    def mapped(self, count, completeness='partial'):
        return {
            'layers': {'competitors': [{'id': f'node/{i}'} for i in range(count)],
                       'drivers': [], 'amenities': []},
            'completeness': completeness,
            'completeness_note_key': 'notes.osm_partial',
            'observed': '2026-09-24',
            'provenance': {'method': 'measured', 'source': 'OpenStreetMap via Overpass'},
        }

    def test_measured_count_is_used_and_carries_its_items(self):
        with patch('geography.nearby', return_value=self.mapped(7)):
            result = advisory.observed_competitors(self.place, 'retail', 10)
        self.assertEqual(result['count'], 7)
        self.assertEqual(len(result['items']), 7, 'count must equal the pins it came from')
        self.assertEqual(result['provenance']['method'], 'measured')

    def test_unsearchable_activity_does_not_masquerade_as_zero_competitors(self):
        with patch('geography.nearby', return_value=self.mapped(0, completeness='unknown')):
            self.assertIsNone(advisory.observed_competitors(self.place, 'other', 10))

    def test_no_coordinates_means_no_measurement(self):
        self.assertIsNone(advisory.observed_competitors({'name': 'X'}, 'retail', 10))

    def test_map_failure_falls_back_rather_than_raising(self):
        with patch('geography.nearby', side_effect=RuntimeError('overpass down')):
            self.assertIsNone(advisory.observed_competitors(self.place, 'retail', 10))

    def test_zero_measured_competitors_is_still_a_measurement(self):
        with patch('geography.nearby', return_value=self.mapped(0)):
            result = advisory.observed_competitors(self.place, 'retail', 10)
        self.assertIsNotNone(result, 'a real zero must not be discarded as "no data"')
        self.assertEqual(result['count'], 0)


if __name__ == '__main__':
    unittest.main()


class ReportsNeverFetch(unittest.TestCase):
    def test_report_path_reads_cache_and_never_calls_the_network(self):
        """A user-facing report must not block on Overpass (and tests must not
        reach it). advisory asks for a cached observation only."""
        seen = {}

        def spy(lat, lon, category, radius_km=15, cache_only=False):
            seen['cache_only'] = cache_only
            return None

        with patch('geography.nearby', side_effect=spy):
            advisory.observed_competitors(CompetitorSource.place, 'retail', 10)
        self.assertTrue(seen.get('cache_only'), 'advisory must request cache_only')
