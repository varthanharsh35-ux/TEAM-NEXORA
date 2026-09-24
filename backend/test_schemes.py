"""Scheme screening regressions; no HTTP or live scheme service is used."""

from copy import deepcopy
from datetime import date
import json
import unittest
from unittest.mock import patch
from urllib.parse import urlparse

from schemes import CATALOG, screen


class SchemeScreening(unittest.TestCase):
    def profile(self, **changes):
        values = {
            "community": "obc", "gender": "female", "age": 29, "income": 180000,
            "project_cost": 400000, "loan_amount": 350000, "sector": "services", "stage": "new",
            "area": "rural", "state": "tamil nadu", "education": "class_12",
            "first_generation": True, "tn_residence_years": 5, "has_capital_expenditure": True,
            "self_financed": False, "constitution": "proprietary", "religion": "hindu",
            "ex_serviceman": False, "person_with_disability": False,
            "sanitation_worker_or_dependant": False, "microenterprise": True,
            "prior_government_subsidy": False, "family_already_assisted": False,
            "pmegp_activity_permitted": True, "extended_gestation": False,
            "weaker_section": False, "shg_member": False, "shg_obc_percentage": 0,
        }
        values.update(changes)
        return values

    def result(self, id, values):
        return next(row for row in screen(values)["schemes"] if row["id"] == id)

    def test_requested_applicants_get_different_sets(self):
        first = self.profile()
        second = self.profile(community="sc", gender="male", age=45, income=600000,
                              project_cost=4000000, loan_amount=3500000)
        def candidates(values):
            return {row["id"] for row in screen(values)["schemes"]
                    if row["status"] in ("eligible", "need_details")}
        self.assertNotEqual(candidates(first), candidates(second))
        self.assertIn("nbcfdc.term", candidates(first))
        self.assertNotIn("nbcfdc.term", candidates(second))

    def test_gender_alone_changes_result(self):
        values = self.profile(community="sc", project_cost=100000, loan_amount=90000)
        self.assertEqual(self.result("nsfdc.mahila_samriddhi", values)["status"], "need_details")
        male = self.result("nsfdc.mahila_samriddhi", {**values, "gender": "male"})
        self.assertEqual(male["status"], "not_eligible")
        self.assertIn("reasons.gender_mismatch", male["reasons"])

    def test_age_alone_changes_result(self):
        values = self.profile(community="sc")
        self.assertEqual(self.result("tahdco.cm_arise", values)["status"], "eligible")
        self.assertEqual(self.result("tahdco.cm_arise", {**values, "age": 56})["status"], "not_eligible")

    def test_sector_alone_changes_result(self):
        values = self.profile(project_cost=2000000, loan_amount=1500000)
        before = self.result("tn.needs", values)
        after = self.result("tn.needs", {**values, "sector": "trading"})
        self.assertNotEqual(before["status"], after["status"])
        self.assertIn("reasons.sector_mismatch", after["reasons"])

    def test_community_is_read(self):
        result = self.result("nsfdc.term", self.profile())
        self.assertIn("reasons.community_mismatch", result["reasons"])

    def test_missing_is_not_rejection(self):
        for row in screen({})["schemes"]:
            with self.subTest(id=row["id"]):
                self.assertIn(row["status"], ("need_details", "withdrawn"))
        result = self.result("tahdco.cm_arise", self.profile(community=None))
        self.assertEqual(result["status"], "need_details")
        self.assertIn("community", result["missing"])

    def test_income_boundary_and_unknown(self):
        values = self.profile(community="sc", income=500000)
        self.assertNotIn("reasons.income_above", self.result("nsfdc.term", values)["reasons"])
        values["income"] += 1
        self.assertIn("reasons.income_above", self.result("nsfdc.term", values)["reasons"])
        self.assertIn("income", self.result("nsfdc.term", self.profile(income=None))["missing"])

    def test_rural_urban_limits_are_independent(self):
        # Synthetic policy isolates the generic engine; it never enters the real catalogue.
        catalog = deepcopy(CATALOG)
        row = catalog["schemes"][0]
        row["eligibility"].update(income_limit_rural=200000, income_limit_urban=400000)
        with patch("schemes.CATALOG", catalog):
            rural = self.result(row["id"], self.profile(community="sc", income=300000,
                                project_cost=100000, loan_amount=90000, area="rural"))
            urban = self.result(row["id"], self.profile(community="sc", income=300000,
                                project_cost=100000, loan_amount=90000, area="urban"))
            unknown = self.result(row["id"], self.profile(community="sc", income=300000,
                                  project_cost=100000, loan_amount=90000, area=None))
        self.assertEqual(rural["status"], "not_eligible")
        self.assertEqual(urban["status"], "need_details")
        self.assertEqual(unknown["status"], "need_details")
        self.assertIn("area", unknown["missing"])

    def test_conflicting_income_boundary_needs_confirmation(self):
        row = self.result("tahdco.cm_arise", self.profile(community="sc", income=300000))
        self.assertEqual(row["status"], "need_details")
        self.assertIn("reasons.confirm_with_agency", row["reasons"])

    def test_stage_is_read(self):
        row = self.result("pmegp.new", self.profile(stage="expansion"))
        self.assertIn("reasons.stage_mismatch", row["reasons"])

    def test_state_is_read(self):
        row = self.result("tn.needs", self.profile(state="kerala", project_cost=2000000))
        self.assertIn("reasons.state_mismatch", row["reasons"])

    def test_education_is_read(self):
        values = self.profile(project_cost=2000000, education="class_8")
        self.assertIn("reasons.education_mismatch", self.result("tn.needs", values)["reasons"])

    def test_pmegp_education_thresholds(self):
        values = self.profile(education="none", sector="services", project_cost=500000)
        self.assertNotIn("reasons.education_mismatch", self.result("pmegp.new", values)["reasons"])
        values["project_cost"] = 500001
        self.assertIn("reasons.education_mismatch", self.result("pmegp.new", values)["reasons"])
        values.update(sector="manufacturing", project_cost=1000000)
        self.assertNotIn("reasons.education_mismatch", self.result("pmegp.new", values)["reasons"])
        values["project_cost"] += 1
        self.assertIn("reasons.education_mismatch", self.result("pmegp.new", values)["reasons"])

    def test_unknown_qualification_is_not_rejection(self):
        values = self.profile(project_cost=2000000, education="diploma")
        result = self.result("tn.needs", values)
        self.assertEqual(result["status"], "need_details")
        self.assertNotIn("reasons.education_mismatch", result["reasons"])

    def test_needs_special_category_age_is_not_general_age(self):
        values = self.profile(community="general", gender="male", age=50, project_cost=2000000)
        self.assertEqual(self.result("tn.needs", values)["status"], "not_eligible")
        values["gender"] = "female"
        row = self.result("tn.needs", values)
        self.assertNotEqual(row["status"], "not_eligible")
        self.assertEqual(row["eligibility"]["age"]["max"], 55)
        self.assertEqual(row["terms"]["beneficiary_share"], .05)

    def test_project_boundaries(self):
        values = self.profile(community="sc", project_cost=140000, loan_amount=125000)
        self.assertNotIn("reasons.project_above_max", self.result("nsfdc.micro", values)["reasons"])
        self.assertIn("reasons.project_below_min", self.result("nsfdc.term", values)["reasons"])
        values["project_cost"] += 1
        self.assertIn("reasons.project_above_max", self.result("nsfdc.micro", values)["reasons"])
        self.assertNotIn("reasons.project_below_min", self.result("nsfdc.term", values)["reasons"])

    def test_savings_are_not_invented_project_cost(self):
        row = self.result("nsfdc.term", {"margin": 100000})
        self.assertIn("project_cost", row["missing"])

    def test_mudra_bands_use_loan_not_project(self):
        values = self.profile(project_cost=2000000, loan_amount=50000)
        self.assertNotEqual(self.result("mudra.shishu", values)["status"], "not_eligible")
        self.assertEqual(self.result("mudra.kishore", values)["status"], "not_eligible")
        values["loan_amount"] = 50001
        self.assertEqual(self.result("mudra.shishu", values)["status"], "not_eligible")
        self.assertNotEqual(self.result("mudra.kishore", values)["status"], "not_eligible")
        values["loan_amount"] = 500000
        self.assertEqual(self.result("mudra.tarun", values)["status"], "not_eligible")
        values["loan_amount"] += 1
        self.assertNotEqual(self.result("mudra.tarun", values)["status"], "not_eligible")

    def test_agriculture_and_allied_are_not_conflated(self):
        row = self.result("mudra.kishore", self.profile(sector="agriculture"))
        self.assertIn("reasons.sector_mismatch", row["reasons"])
        row = self.result("mudra.kishore", self.profile(sector="dairy"))
        self.assertNotIn("reasons.sector_mismatch", row["reasons"])

    def test_disability_and_occupation_not_inferred_from_caste(self):
        for id, field in [("nhfdc.swavalamban", "person_with_disability"),
                          ("nskfdc.term", "sanitation_worker_or_dependant")]:
            self.assertEqual(self.result(id, self.profile(**{field: False}))["status"], "not_eligible")
            self.assertEqual(self.result(id, self.profile(**{field: None}))["status"], "need_details")
            self.assertEqual(self.result(id, self.profile(**{field: True}))["status"], "need_details")

    def test_nmdfc_religion_is_separate_from_community(self):
        values = self.profile(community="obc", religion="muslim")
        self.assertNotEqual(self.result("nmdfc.term_cl1", values)["status"], "not_eligible")
        values["religion"] = "hindu"
        self.assertEqual(self.result("nmdfc.term_cl1", values)["status"], "not_eligible")

    def test_nbcfdc_shg_exception(self):
        values = self.profile(community="sc", loan_amount=100000, weaker_section=True,
                              shg_member=True, shg_obc_percentage=60)
        self.assertNotEqual(self.result("nbcfdc.micro", values)["status"], "not_eligible")
        values["shg_obc_percentage"] = 59
        self.assertEqual(self.result("nbcfdc.micro", values)["status"], "not_eligible")

    def test_variable_rates_not_guessed(self):
        self.assertEqual(self.result("nbcfdc.term", self.profile(loan_amount=125000))["terms"]["interest_rate"], 7)
        self.assertEqual(self.result("nbcfdc.term", self.profile(loan_amount=125001))["terms"]["interest_rate"], 8)
        self.assertIsNone(self.result("nbcfdc.term", self.profile(loan_amount=None))["terms"]["interest_rate"])
        self.assertIsNone(self.result("mudra.kishore", self.profile())["terms"]["interest_rate"])

    def test_variable_grace_not_guessed(self):
        values = self.profile(community="sc", extended_gestation=True)
        self.assertEqual(self.result("nsfdc.term", values)["terms"]["moratorium_months"], 12)
        values["extended_gestation"] = None
        self.assertIsNone(self.result("nsfdc.term", values)["terms"]["moratorium_months"])

    def test_withdrawn_remains_visible(self):
        row = self.result("stand_up_india", {})
        self.assertEqual(row["status"], "withdrawn")
        self.assertEqual(row["withdrawn_on"], "2025-03-31")
        self.assertIn("reasons.scheme_withdrawn", row["reasons"])

    def test_invalid_numbers_remain_unknown(self):
        for value in (True, -1, "bad", float("nan"), float("inf")):
            row = self.result("tahdco.cm_arise", self.profile(community="sc", age=value))
            self.assertEqual(row["status"], "need_details")
            self.assertIn("reasons.invalid_input", row["reasons"])
        for value in (0, -1, "NaN"):
            row = self.result("nsfdc.micro", self.profile(community="sc", loan_amount=90000, project_cost=value))
            self.assertEqual(row["status"], "need_details")

    def test_input_aliases(self):
        row = self.result("tahdco.cm_arise", {
            "community": " SC ", "gender": "woman", "age": "29", "household_income": "180000",
            "business_stage": "new", "state": "TN", "category": "dairy",
        })
        self.assertEqual(row["status"], "eligible")

    def test_screen_does_not_mutate_catalog_or_input(self):
        before = deepcopy(CATALOG)
        values = self.profile(project_cost=2000000)
        original = deepcopy(values)
        screen(values)
        self.assertEqual(values, original)
        self.assertEqual(CATALOG, before)

    def test_full_shape_sources_and_dates(self):
        self.assertEqual(len(CATALOG["schemes"]), 15)
        ids = [row["id"] for row in CATALOG["schemes"]]
        self.assertEqual(len(ids), len(set(ids)))
        expected = {"beneficiary_share", "agency_share", "project_min", "project_max", "loan_cap",
                    "interest_rate", "tenure_months", "moratorium_months", "subsidy"}
        for row in CATALOG["schemes"]:
            self.assertEqual(set(row["terms"]), expected)
            self.assertTrue(urlparse(row["source_url"]).netloc)
            date.fromisoformat(row["verified_on"])
            self.assertIn("education", row["eligibility"])
            self.assertIn("withdrawn_on", row)
            self.assertIsInstance(row["documents"], list)
            self.assertEqual(row["provenance"]["source_url"], row["source_url"])

    def test_numeric_terms_always_have_sources(self):
        def numbers(value):
            if isinstance(value, dict):
                return any(numbers(child) for child in value.values())
            if isinstance(value, list):
                return any(numbers(child) for child in value)
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        for row in screen(self.profile())["schemes"]:
            if numbers(row["terms"]) or numbers(row.get("term_options", [])):
                self.assertTrue(row["source_url"])
                self.assertTrue(row["verified_on"])

    def test_unverified_fields_are_null(self):
        for row in CATALOG["schemes"]:
            for path in row["unverified"]:
                value = row
                for part in path.split("."):
                    value = value[part]
                # An unverified document checklist is represented by an empty array per contract.
                self.assertIn(value, (None, []), (row["id"], path))

    def test_response_is_json_and_status_contract(self):
        response = screen(self.profile())
        json.dumps(response, allow_nan=False)
        self.assertEqual(set(response), {"schemes", "freshness"})
        self.assertEqual(response["freshness"]["dataset"], "schemes")
        for row in response["schemes"]:
            self.assertIn(row["status"], {"eligible", "need_details", "not_eligible", "withdrawn"})
            self.assertTrue(all(reason.startswith("reasons.") for reason in row["reasons"]))


if __name__ == "__main__":
    unittest.main()
