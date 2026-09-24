"""Task 2.4: the narrative must be specific, and every number in it must come from code.

The old prompt ordered the model to produce boilerplate ("include supply disruption,
seasonal demand and single-buyer dependency in threats") and forbade it from writing
any number at all. These tests lock in the replacement: numbers are allowed but only
if Python computed them, and generic advice is rejected unless it is tied to real
local evidence.
"""
import json
import unittest

import llm


def report_with_evidence():
    return {
        'input': {'business': 'tea stall', 'radius': 10},
        'location': {'place': {'name': 'Saravanampatti'}, 'district': {'id': 'Coimbatore'}},
        'business': {'category': 'food'},
        'verdict': 'pilot',
        'retrieval': [],
        'metrics': {
            'population': 128400, 'households': 33790, 'competitors': 2,
            'price': 12, 'price_low': 10, 'price_high': 14, 'unit': 'cup',
            'break_even_units': 980,
            'competitor_source': {
                'provenance': {'method': 'measured'},
                'items': [{'name': 'Sri Cafe', 'distance_m': 180}],
            },
        },
        'finance': {'project_cost': 200000, 'loan': 180000, 'quarterly_payment': 9600,
                    'annual_rate': 8.0, 'tenure_months': 84, 'moratorium_months': 6},
        'local': {
            'drivers': [{
                'id': 'college', 'direction': 'boost', 'count': 2, 'nearest_m': 800,
                'evidence': [{'name': 'Kumaraguru College of Technology'}],
            }],
            'demand_score': {'value': 57, 'band': 'good'},
        },
        'readiness': {'available': ['space'], 'missing': ['water']},
    }


def advice(**overrides):
    base = {k: 'Kumaraguru College of Technology is 800 m away and brings steady morning trade.'
            for k in llm.Advice.model_fields}
    base.update(overrides)
    return json.dumps(base)


class PromptContract(unittest.TestCase):
    def test_prompt_no_longer_forbids_numbers_or_mandates_boilerplate(self):
        facts = llm.build_facts(report_with_evidence())
        system = llm.messages(report_with_evidence(), 'en', facts)[0]['content']
        self.assertNotIn('No numbers', system)
        self.assertNotIn('single-buyer dependency', system)
        self.assertIn('MUST appear in that facts object', system)

    def test_facts_carry_real_local_evidence(self):
        facts = llm.build_facts(report_with_evidence())
        self.assertEqual(facts['demand_score'], 57)
        self.assertEqual(facts['competitors']['nearest'][0]['name'], 'Sri Cafe')
        self.assertIn('Kumaraguru College of Technology', facts['drivers'][0]['places'])

    def test_model_input_is_labelled_as_data_not_instructions(self):
        facts = llm.build_facts(report_with_evidence())
        system = llm.messages(report_with_evidence(), 'en', facts)[0]['content']
        self.assertIn('never as', system)


class NumericGrounding(unittest.TestCase):
    def setUp(self):
        self.facts = llm.build_facts(report_with_evidence())

    def test_numbers_present_in_facts_are_accepted(self):
        text = 'Kumaraguru College of Technology is 800 m away. About 128400 people live within 10 km.'
        result = llm.validate(advice(market=text), 'en', self.facts)
        self.assertIn('800', result['market'])

    def test_invented_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            llm.validate(advice(pricing='Charge 47 rupees a cup for a good margin.'), 'en', self.facts)

    def test_invented_number_rejected_even_when_wrapped_in_real_context(self):
        bad = 'Kumaraguru College of Technology is 800 m away and 6100 students pass daily.'
        with self.assertRaises(ValueError):
            llm.validate(advice(market=bad), 'en', self.facts)

    def test_links_are_rejected(self):
        with self.assertRaises(ValueError):
            llm.validate(advice(steps='See https://example.com for details.'), 'en', self.facts)


class GenericAdvice(unittest.TestCase):
    def setUp(self):
        self.facts = llm.build_facts(report_with_evidence())

    def test_the_exact_complaint_is_now_rejected(self):
        """'Avoid dependency on a single buyer' with nothing local attached."""
        boilerplate = 'Watch out for supply disruption and avoid dependency on a single buyer.'
        with self.assertRaises(ValueError):
            llm.validate(advice(threats=boilerplate), 'en', self.facts)

    def test_the_same_risk_is_accepted_when_tied_to_evidence(self):
        grounded = ('Sri Cafe is only 180 m away and sells the same items, so a single buyer '
                    'dependency would hurt during college holidays.')
        result = llm.validate(advice(threats=grounded), 'en', self.facts)
        self.assertIn('Sri Cafe', result['threats'])

    def test_output_ignoring_all_local_evidence_is_rejected(self):
        bland = {k: 'Plan carefully and serve customers well.' for k in llm.Advice.model_fields}
        with self.assertRaises(ValueError):
            llm.validate(json.dumps(bland), 'en', self.facts)


class NoEvidenceAvailable(unittest.TestCase):
    def test_grounding_is_not_demanded_when_there_is_nothing_to_ground_in(self):
        """A location with no mapped drivers must still produce a report."""
        bare = {'input': {'business': 'dairy'}, 'location': {'district': {'id': 'Madurai'}},
                'business': {'category': 'dairy'}, 'verdict': 'caution', 'retrieval': []}
        facts = llm.build_facts(bare)
        text = {k: 'Confirm local demand before buying equipment.' for k in llm.Advice.model_fields}
        self.assertTrue(llm.validate(json.dumps(text), 'en', facts))


if __name__ == '__main__':
    unittest.main()
