"""Task 3.5: Inventory and setup plan.

Implements DATA_CONTRACT.md §5 — POST /api/inventory/plan.

Per-activity item lists live in data/inventory.json.  Items the user
already owns are listed with already_owned: true and excluded from
totals — shown, not hidden.  One-time and recurring costs are separated.

Every cost is an estimate from curated sector priors.  Provenance is
attached to every item (rule 4).
"""

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "inventory.json"

_PROVENANCE = {
    "method": "estimated",
    "source": "curated-sector-priors",
}


def _money(x):
    return float(Decimal(str(x)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP))


def _load_catalog():
    """Load inventory catalog from data/inventory.json."""
    text = DATA_FILE.read_text(encoding="utf-8")
    catalog = json.loads(text)
    # Strip the _meta key, keep only sectors
    return {k: v for k, v in catalog.items() if k != "_meta"}


def plan(activity_id, facilities_owned=None, quantity_overrides=None):
    """Build an inventory plan for the given activity.

    Parameters
    ----------
    activity_id : str
        Sector or activity key (e.g. "poultry", "food.cafe").
        Falls through to the sector part before the dot.
    facilities_owned : list[str] | None
        Facility IDs the user already owns (e.g. ["space", "power"]).
        Matched against item ids to mark already_owned.
    quantity_overrides : dict[str, int] | None
        User-supplied quantities keyed by item id.

    Returns
    -------
    dict
        The inventory plan matching DATA_CONTRACT.md §5.
    """
    if facilities_owned is None:
        facilities_owned = []
    if quantity_overrides is None:
        quantity_overrides = {}

    catalog = _load_catalog()

    # Resolve activity to sector: "food.cafe" -> "food", "poultry" -> "poultry"
    sector = activity_id.split(".")[0] if activity_id else "other"
    sector_data = catalog.get(sector, catalog.get("other"))
    if sector_data is None:
        sector_data = catalog["other"]

    items_spec = sector_data["items"]
    contingency_pct = sector_data.get("contingency_pct", 10)
    wc_months = sector_data.get("working_capital_months", 3)

    # Map facility keywords to item IDs for already_owned matching.
    # The facilities list from the user profile uses broad terms like
    # "space", "power", "equipment", "cold", "transport", "storage",
    # "water", "three_phase".  Map them to the item ids they cover.
    _FACILITY_TO_ITEMS = {
        "space": {"cattle_shed", "poultry_shed", "fish_pond"},
        "power": {"electricity"},
        "three_phase": {"electricity"},
        "equipment": {
            "sewing_machine", "overlock", "milking_machine",
            "cooking_range", "compressor", "machinery",
            "tool_kit", "pump_set", "aerator", "equipment",
        },
        "cold": {"refrigerator", "ice_box"},
        "transport": {"vehicle", "transport"},
        "storage": {"shelving"},
        "water": {"drip_kit"},
    }

    owned_item_ids = set()
    for facility in facilities_owned:
        mapped = _FACILITY_TO_ITEMS.get(facility, set())
        owned_item_ids.update(mapped)

    items = []
    one_time_total = Decimal("0")
    recurring_monthly = Decimal("0")

    for spec in items_spec:
        item_id = spec["id"]
        quantity = quantity_overrides.get(item_id, spec["quantity"])
        if quantity < 0:
            quantity = spec["quantity"]
        unit_cost = Decimal(str(spec["unit_cost"]))
        total = Decimal(str(quantity)) * unit_cost
        already_owned = item_id in owned_item_ids

        item = {
            "id": item_id,
            "label_key": spec["label_key"],
            "emoji": spec["emoji"],
            "quantity": quantity,
            "unit_cost": _money(unit_cost),
            "total": _money(total),
            "kind": spec["kind"],
            "already_owned": already_owned,
            "provenance": dict(_PROVENANCE),
        }
        items.append(item)

        # Owned items are shown but excluded from totals
        if not already_owned:
            if spec["kind"] == "one_time":
                one_time_total += total
            else:
                recurring_monthly += total

    working_capital = recurring_monthly * Decimal(str(wc_months))
    contingency = one_time_total * Decimal(str(contingency_pct)) / Decimal("100")
    project_cost = one_time_total + working_capital + contingency

    return {
        "items": items,
        "one_time_total": _money(one_time_total),
        "recurring_monthly": _money(recurring_monthly),
        "working_capital": _money(working_capital),
        "contingency": _money(contingency),
        "project_cost": _money(project_cost),
    }
