"""Task 3.5: tests for inventory and setup plan."""
import unittest

import inventory


class InventoryPlanBasics(unittest.TestCase):
    """Core behaviour: items, totals, provenance."""

    def test_plan_returns_items_for_known_sector(self):
        result = inventory.plan("poultry")
        self.assertIn("items", result)
        self.assertGreater(len(result["items"]), 0)

    def test_plan_returns_items_for_dotted_activity(self):
        """'food.cafe' should resolve to the 'food' sector."""
        result = inventory.plan("food.cafe")
        self.assertGreater(len(result["items"]), 0)

    def test_plan_falls_back_to_other_for_unknown(self):
        result = inventory.plan("quantum_farming")
        self.assertGreater(len(result["items"]), 0)

    def test_plan_returns_contract_shape(self):
        """DATA_CONTRACT.md §5 required fields."""
        result = inventory.plan("dairy")
        self.assertIn("items", result)
        self.assertIn("one_time_total", result)
        self.assertIn("recurring_monthly", result)
        self.assertIn("working_capital", result)
        self.assertIn("contingency", result)
        self.assertIn("project_cost", result)

    def test_every_item_has_required_fields(self):
        result = inventory.plan("food")
        required = {"id", "label_key", "emoji", "quantity", "unit_cost",
                     "total", "kind", "already_owned", "provenance"}
        for item in result["items"]:
            self.assertTrue(
                required.issubset(item.keys()),
                f"item {item.get('id')} missing fields: "
                f"{required - item.keys()}",
            )

    def test_every_item_carries_provenance(self):
        """Rule 4: every number needs provenance."""
        result = inventory.plan("retail")
        for item in result["items"]:
            self.assertIn("provenance", item)
            self.assertIn("method", item["provenance"])
            self.assertEqual(item["provenance"]["method"], "estimated")
            self.assertIn("source", item["provenance"])


class OneTimeVsRecurring(unittest.TestCase):

    def test_kinds_are_separated(self):
        result = inventory.plan("food")
        kinds = {item["kind"] for item in result["items"]}
        self.assertIn("one_time", kinds)
        self.assertIn("recurring", kinds)

    def test_one_time_total_matches_items(self):
        result = inventory.plan("poultry")
        expected = sum(
            item["total"] for item in result["items"]
            if item["kind"] == "one_time" and not item["already_owned"]
        )
        self.assertAlmostEqual(result["one_time_total"], expected, places=2)

    def test_recurring_monthly_matches_items(self):
        result = inventory.plan("dairy")
        expected = sum(
            item["total"] for item in result["items"]
            if item["kind"] == "recurring" and not item["already_owned"]
        )
        self.assertAlmostEqual(result["recurring_monthly"], expected, places=2)


class OwnedItemDeduction(unittest.TestCase):
    """Items the user already owns: shown but excluded from totals."""

    def test_owned_items_are_shown_not_hidden(self):
        result = inventory.plan("poultry", facilities_owned=["power"])
        elec = [i for i in result["items"] if i["id"] == "electricity"]
        self.assertEqual(len(elec), 1, "electricity item must still appear")
        self.assertTrue(elec[0]["already_owned"])

    def test_owned_items_excluded_from_totals(self):
        without = inventory.plan("food")
        with_owned = inventory.plan("food", facilities_owned=["power"])

        # The electricity recurring cost should be deducted
        self.assertLess(
            with_owned["recurring_monthly"],
            without["recurring_monthly"],
        )

    def test_owned_equipment_deducted(self):
        without = inventory.plan("repair")
        with_equip = inventory.plan("repair", facilities_owned=["equipment"])

        tool_without = next(
            i for i in without["items"] if i["id"] == "tool_kit"
        )
        tool_with = next(
            i for i in with_equip["items"] if i["id"] == "tool_kit"
        )
        self.assertFalse(tool_without["already_owned"])
        self.assertTrue(tool_with["already_owned"])

    def test_project_cost_is_lower_when_items_owned(self):
        without = inventory.plan("dairy")
        with_owned = inventory.plan(
            "dairy", facilities_owned=["equipment", "power"],
        )
        self.assertLess(with_owned["project_cost"], without["project_cost"])


class ProjectCostArithmetic(unittest.TestCase):

    def test_project_cost_equals_sum_of_components(self):
        result = inventory.plan("tailoring")
        expected = (
            result["one_time_total"]
            + result["working_capital"]
            + result["contingency"]
        )
        self.assertAlmostEqual(result["project_cost"], expected, places=2)

    def test_working_capital_is_three_months_recurring(self):
        result = inventory.plan("retail")
        self.assertAlmostEqual(
            result["working_capital"],
            result["recurring_monthly"] * 3,
            places=2,
        )

    def test_contingency_is_ten_percent_of_one_time(self):
        result = inventory.plan("fish")
        self.assertAlmostEqual(
            result["contingency"],
            result["one_time_total"] * 0.10,
            places=2,
        )


class QuantityOverrides(unittest.TestCase):

    def test_user_can_override_quantity(self):
        result = inventory.plan("poultry", quantity_overrides={"chicks": 1000})
        chicks = next(i for i in result["items"] if i["id"] == "chicks")
        self.assertEqual(chicks["quantity"], 1000)
        self.assertEqual(chicks["total"], 1000 * 45)

    def test_negative_override_is_ignored(self):
        result = inventory.plan("poultry", quantity_overrides={"chicks": -5})
        chicks = next(i for i in result["items"] if i["id"] == "chicks")
        self.assertEqual(chicks["quantity"], 500)  # default from catalog


class AllSectors(unittest.TestCase):
    """Every sector in the catalog should produce a valid plan."""

    def test_all_sectors_produce_valid_plans(self):
        catalog = inventory._load_catalog()
        for sector in catalog:
            with self.subTest(sector=sector):
                result = inventory.plan(sector)
                self.assertGreater(len(result["items"]), 0)
                self.assertGreater(result["project_cost"], 0)
                self.assertGreaterEqual(result["one_time_total"], 0)
                self.assertGreaterEqual(result["recurring_monthly"], 0)


if __name__ == "__main__":
    unittest.main()
