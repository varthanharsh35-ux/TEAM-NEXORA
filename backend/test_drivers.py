"""Task 2.1: the local demand driver engine.

The test that matters is test_two_locations_differ. If the same activity in two
different places produces the same drivers and the same score, the engine is not
working, however plausible its output looks.
"""
import unittest

import drivers


def poi(kind, name, distance_m, url='https://www.openstreetmap.org/node/1'):
    return {'kind': kind, 'name': name, 'distance_m': distance_m, 'source_url': url}


def rival(distance_m, match='direct', name='Existing shop'):
    return {'distance_m': distance_m, 'match': match, 'name': name, 'id': f'node/{distance_m}'}


class Classification(unittest.TestCase):
    def test_known_kinds_classify(self):
        self.assertEqual(drivers.classify({'amenity': 'college'}), 'college')
        self.assertEqual(drivers.classify({'amenity': 'bus_station'}), 'bus_stand')
        self.assertEqual(drivers.classify({'railway': 'station'}), 'railway')

    def test_blood_bank_is_not_a_driver(self):
        self.assertIsNone(drivers.classify({'amenity': 'blood_bank'}))

    def test_plain_bank_is_not_a_driver(self):
        # Banks are amenities. They must not influence the score.
        self.assertIsNone(drivers.classify({'amenity': 'bank'}))

    def test_every_selector_in_the_data_file_is_parseable(self):
        for selector in drivers.all_selectors():
            drivers.matches({'x': 'y'}, selector)


class Scoring(unittest.TestCase):
    def test_no_drivers_scores_fifty(self):
        result = drivers.score('food', [], [])
        self.assertEqual(result['demand_score']['value'], 50)
        self.assertEqual(result['demand_score']['band'], 'fair')

    def test_distance_reduces_effect(self):
        near = drivers.score('food', [poi('college', 'A', 100)], [])
        far = drivers.score('food', [poi('college', 'A', 3000)], [])
        self.assertGreater(near['demand_score']['value'], far['demand_score']['value'])

    def test_driver_without_a_name_is_not_emitted(self):
        """We do not claim a college exists if we cannot say which one."""
        result = drivers.score('food', [poi('college', '', 200)], [])
        self.assertEqual(result['drivers'], [])
        self.assertEqual(result['demand_score']['value'], 50)

    def test_every_emitted_driver_carries_evidence(self):
        result = drivers.score('food', [poi('college', 'KCT', 800), poi('hostel', 'Boys Hostel', 400)], [])
        self.assertTrue(result['drivers'])
        for driver in result['drivers']:
            self.assertTrue(driver['evidence'], f"{driver['id']} has no evidence")
            for item in driver['evidence']:
                self.assertTrue(item['name'])

    def test_competitors_suppress(self):
        alone = drivers.score('food', [poi('college', 'KCT', 500)], [])
        crowded = drivers.score('food', [poi('college', 'KCT', 500)], [rival(150), rival(200)])
        self.assertLess(crowded['demand_score']['value'], alone['demand_score']['value'])

    def test_adjacent_competitors_count_less_than_direct(self):
        direct = drivers.score('retail', [], [rival(300, 'direct')])
        adjacent = drivers.score('retail', [], [rival(300, 'adjacent')])
        self.assertLess(direct['demand_score']['value'], adjacent['demand_score']['value'])

    def test_score_is_capped_within_range(self):
        many = [poi('college', f'College {i}', 50) for i in range(40)]
        result = drivers.score('food', many, [])
        self.assertLessEqual(result['demand_score']['value'], 100)
        self.assertGreaterEqual(result['demand_score']['value'], 0)

    def test_weights_are_sector_specific(self):
        """A college helps a cafe far more than it helps a warehouse."""
        cafe = drivers.score('food', [poi('college', 'KCT', 400)], [])
        warehouse = drivers.score('warehousing', [poi('college', 'KCT', 400)], [])
        self.assertGreater(cafe['demand_score']['value'], warehouse['demand_score']['value'])

    def test_components_sum_to_the_score(self):
        result = drivers.score('food', [poi('college', 'KCT', 500)], [rival(300)])
        parts = result['demand_score']['components']
        expected = max(0, min(100, round(50 * (1 + parts['boost'] + parts['suppress']))))
        self.assertEqual(result['demand_score']['value'], expected)


class WorkedExamples(unittest.TestCase):
    """The scenarios in docs/PERSONALIZATION.md section 4."""

    def test_cafe_near_colleges_scores_well(self):
        result = drivers.score('food', [
            poi('college', 'Kumaraguru College of Technology', 800),
            poi('college', 'Sri Krishna College', 900),
            poi('college', 'Hindusthan College', 1100),
            poi('it_park', 'Tidel Park', 1200),
        ], [rival(180), rival(190)])
        self.assertGreaterEqual(result['demand_score']['value'], 55)
        self.assertEqual(result['demand_score']['band'], 'good')

    def test_warehouse_near_fulfilment_centre_is_dragged_down(self):
        near_fc = drivers.score('warehousing', [
            poi('highway_access', 'NH 544', 1000),
            poi('anchor_logistics', 'Amazon Fulfilment Centre', 4000),
        ], [])
        without = drivers.score('warehousing', [poi('highway_access', 'NH 544', 1000)], [])
        self.assertLess(near_fc['demand_score']['value'], without['demand_score']['value'])

    def test_poultry_near_worship_cluster_is_suppressed(self):
        result = drivers.score('poultry', [
            poi('place_of_worship', 'Perundurai Temple', 1400),
            poi('feed_supplier', 'Annur Feeds', 3000),
        ], [])
        kinds = {d['id']: d for d in result['drivers']}
        self.assertEqual(kinds['place_of_worship']['direction'], 'suppress')
        self.assertEqual(kinds['feed_supplier']['direction'], 'boost')


class TwoLocations(unittest.TestCase):
    def test_two_locations_differ(self):
        """The test that proves the engine works at all.

        Same activity, two different neighbourhoods: the driver lists and the
        scores must both differ. If they do not, the engine is returning a
        constant dressed up as analysis.
        """
        campus = drivers.score('food', [
            poi('college', 'Kumaraguru College', 700),
            poi('hostel', 'Mens Hostel', 500),
            poi('bus_stand', 'Saravanampatti Bus Stop', 300),
        ], [rival(600, name='Campus Tea Stall')])
        remote = drivers.score('food', [
            poi('place_of_worship', 'Village Temple', 900),
            poi('market', 'Weekly Market', 2500),
        ], [rival(120, name='Village Mess'), rival(180, name='Anna Tiffin'),
            rival(240, name='Corner Kadai')])

        self.assertNotEqual(
            {d['id'] for d in campus['drivers']},
            {d['id'] for d in remote['drivers']},
            'driver lists must differ between locations',
        )
        self.assertNotEqual(
            campus['demand_score']['value'],
            remote['demand_score']['value'],
            'scores must differ between locations',
        )
        self.assertGreater(campus['demand_score']['value'], remote['demand_score']['value'])

        campus_names = {e['name'] for d in campus['drivers'] for e in d['evidence']}
        remote_names = {e['name'] for d in remote['drivers'] for e in d['evidence']}
        self.assertFalse(campus_names & remote_names, 'evidence must be location-specific')


if __name__ == '__main__':
    unittest.main()
