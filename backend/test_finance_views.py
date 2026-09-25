"""Task 3.6: tests for split finance routes."""
import unittest
from finance import calculate
from finance_views import overview, allocation, repayment, _verdict


class VerdictLogic(unittest.TestCase):

    def test_green_when_no_issues(self):
        v = _verdict({})
        self.assertEqual(v["light"], "green")
        self.assertEqual(v["label"], "go")

    def test_amber_on_caution(self):
        v = _verdict({
            "caution": True,
            "caution_reason_key": "test.caution",
            "caution_params": {"x": 1},
        })
        self.assertEqual(v["light"], "amber")
        self.assertEqual(v["label"], "caution")

    def test_red_on_blocker(self):
        v = _verdict({
            "blocker": True,
            "blocker_reason_key": "test.blocker",
            "blocker_params": {},
        })
        self.assertEqual(v["light"], "red")
        self.assertEqual(v["label"], "blocker")

    def test_blocker_overrides_caution(self):
        v = _verdict({
            "blocker": True,
            "blocker_reason_key": "test.blocker",
            "caution": True,
            "caution_reason_key": "test.caution",
        })
        self.assertEqual(v["light"], "red")


class OverviewTests(unittest.TestCase):

    def test_overview_returns_verdict(self):
        result = overview(100000, "2026-10-01")
        self.assertIn("verdict", result)
        self.assertIn("light", result["verdict"])
        self.assertIn(result["verdict"]["light"], ("green", "amber", "red"))

    def test_overview_matches_calculate(self):
        calc = calculate(100000, "2026-10-01")
        ov = overview(100000, "2026-10-01")
        self.assertEqual(ov["project_cost"], calc["project_cost"])
        self.assertEqual(ov["loan"], calc["loan"])
        self.assertEqual(ov["scheme"], calc["scheme"])
        self.assertEqual(ov["margin"], calc["margin"])
        self.assertEqual(ov["annual_rate"], calc["annual_rate"])

    def test_overview_green_when_fully_funded(self):
        ov = overview(100000, "2026-10-01")
        self.assertEqual(ov["verdict"]["light"], "green")

    def test_overview_red_when_outside_scheme(self):
        ov = overview(500001, "2026-10-01")
        self.assertEqual(ov["verdict"]["light"], "red")

    def test_overview_amber_when_cap_applied(self):
        ov = overview(14000, "2026-10-01")
        self.assertTrue(ov["cap_applied"])
        self.assertEqual(ov["verdict"]["light"], "amber")

    def test_overview_has_assumptions(self):
        ov = overview(100000, "2026-10-01")
        self.assertIsInstance(ov["assumptions"], list)
        self.assertTrue(len(ov["assumptions"]) > 0)
        for a in ov["assumptions"]:
            self.assertIn("key", a)
            self.assertIn("confirm_with", a)


class AllocationTests(unittest.TestCase):

    def test_allocation_returns_verdict(self):
        result = allocation(100000, "2026-10-01")
        self.assertIn("verdict", result)

    def test_allocation_percentages_sum_to_100(self):
        result = allocation(100000, "2026-10-01")
        total_pct = result["margin_pct"] + result["loan_pct"] + result["gap_pct"]
        self.assertAlmostEqual(total_pct, 100.0, places=0)

    def test_allocation_margin_and_loan_match_calculate(self):
        calc = calculate(100000, "2026-10-01")
        alloc = allocation(100000, "2026-10-01")
        self.assertEqual(alloc["project_cost"], calc["project_cost"])
        self.assertEqual(alloc["margin"], calc["margin"])
        self.assertEqual(alloc["loan"], calc["loan"])

    def test_allocation_includes_inventory_when_activity_given(self):
        alloc = allocation(100000, "2026-10-01", activity_id="poultry")
        self.assertIn("inventory", alloc)
        self.assertIn("items", alloc["inventory"])
        self.assertIn("project_cost", alloc["inventory"])

    def test_allocation_no_inventory_without_activity(self):
        alloc = allocation(100000, "2026-10-01")
        self.assertNotIn("inventory", alloc)

    def test_allocation_red_when_gap_exists(self):
        # Force a scenario with a gap via project_cost override
        alloc = allocation(10000, "2026-10-01", project_cost=5000000)
        if alloc["funding_gap"] > 0:
            self.assertEqual(alloc["verdict"]["light"], "red")


class RepaymentTests(unittest.TestCase):

    def test_repayment_returns_verdict(self):
        result = repayment(100000, "2026-10-01")
        self.assertIn("verdict", result)

    def test_repayment_has_split_schedules(self):
        result = repayment(100000, "2026-10-01")
        self.assertIn("moratorium_schedule", result)
        self.assertIn("repayment_schedule", result)
        self.assertIn("schedule", result)
        # Moratorium quarters have zero payment
        for q in result["moratorium_schedule"]:
            self.assertEqual(q["payment"], 0)
            self.assertTrue(q["moratorium"])
        # Repayment quarters have nonzero payment
        for q in result["repayment_schedule"]:
            self.assertGreater(q["payment"], 0)
            self.assertFalse(q["moratorium"])

    def test_repayment_matches_calculate(self):
        calc = calculate(100000, "2026-10-01")
        rep = repayment(100000, "2026-10-01")
        self.assertEqual(rep["loan"], calc["loan"])
        self.assertEqual(rep["quarterly_payment"], calc["quarterly_payment"])
        self.assertEqual(rep["total_interest"], calc["total_interest"])
        self.assertEqual(rep["total_repayment"], calc["total_repayment"])
        self.assertEqual(rep["schedule"], calc["schedule"])

    def test_repayment_has_monthly_equivalent(self):
        rep = repayment(100000, "2026-10-01")
        self.assertIn("monthly_equivalent", rep)
        self.assertAlmostEqual(
            rep["monthly_equivalent"],
            round(rep["quarterly_payment"] / 3, 2),
            places=2,
        )

    def test_repayment_has_assumptions(self):
        rep = repayment(100000, "2026-10-01")
        self.assertIsInstance(rep["assumptions"], list)
        self.assertGreaterEqual(len(rep["assumptions"]), 2)

    def test_self_funded_is_green(self):
        rep = repayment(100000, "2026-10-01", project_cost=50000)
        self.assertEqual(rep["verdict"]["light"], "green")
        self.assertEqual(rep["loan"], 0)

    def test_outside_scheme_is_red(self):
        rep = repayment(500001, "2026-10-01")
        self.assertEqual(rep["verdict"]["light"], "red")


class ConsistencyAcrossViews(unittest.TestCase):
    """Rule 5: same number computed once, never two different ways."""

    def test_all_three_views_agree_on_core_numbers(self):
        margin = 100000
        start = "2026-10-01"
        ov = overview(margin, start)
        alloc = allocation(margin, start)
        rep = repayment(margin, start)

        # All three derive from the same calculate() call
        self.assertEqual(ov["project_cost"], alloc["project_cost"])
        self.assertEqual(ov["loan"], alloc["loan"])
        self.assertEqual(ov["loan"], rep["loan"])
        self.assertEqual(ov["annual_rate"], rep["annual_rate"])
        self.assertEqual(ov["tenure_months"], rep["tenure_months"])

    def test_micro_scheme_consistent(self):
        margin = 14000
        ov = overview(margin)
        alloc = allocation(margin)
        rep = repayment(margin)
        self.assertEqual(ov["scheme"], "micro")
        self.assertEqual(alloc["scheme"], "micro")
        self.assertEqual(ov["loan"], rep["loan"])


if __name__ == "__main__":
    unittest.main()
