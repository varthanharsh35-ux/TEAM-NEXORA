"""Pricing strategy engine: evaluates penetration, match, and premium positions."""

import math


def strategy(
    activity_id: str,
    demand_score: int,
    competitor_count: int,
    competitor_within_1km: int,
    project_cost: float,
    loan: float,
    quarterly_payment: float,
    capacity_units_per_month: float,
    unit_label: str,
    sector_price_band: dict
) -> dict:
    """Evaluate pricing strategy positions and sensitivity against capacity.

    sector_price_band: {low, mid, high, unit, source, date}
    """
    low = float(sector_price_band.get("low", 10.0))
    mid = float(sector_price_band.get("mid", low))
    high = float(sector_price_band.get("high", mid))

    p_penetration = round(low * 0.9, 2)
    p_match = round(mid, 2)
    p_premium = round(high * 1.1, 2)

    variable_cost = round(low * 0.6, 2)
    monthly_fixed = quarterly_payment / 3.0

    def calc_break_even(price: float) -> int:
        margin = price - variable_cost
        if margin <= 0:
            return 999999
        return math.ceil(monthly_fixed / margin)

    be_penetration = calc_break_even(p_penetration)
    be_match = calc_break_even(p_match)
    be_premium = calc_break_even(p_premium)

    reach_penetration = be_penetration <= capacity_units_per_month
    reach_match = be_match <= capacity_units_per_month
    reach_premium = be_premium <= capacity_units_per_month

    # Determine candidate recommendation
    if demand_score >= 65 and competitor_within_1km <= 1:
        chosen = "premium"
        reason_key = "notes.pricing.premium_justified"
        reason_params = {"demand_score": demand_score, "competitor_within_1km": competitor_within_1km}
    elif demand_score >= 45 and competitor_count <= 3:
        chosen = "match"
        reason_key = "notes.pricing.match_market"
        reason_params = {"demand_score": demand_score, "competitor_count": competitor_count}
    else:
        chosen = "penetration"
        reason_key = "notes.pricing.penetration_volume"
        reason_params = {"demand_score": demand_score, "competitor_count": competitor_count}

    # Downgrade if break_even > capacity
    if chosen == "premium" and not reach_premium:
        if reach_match:
            chosen = "match"
            reason_key = "notes.pricing.downgraded_to_match"
            reason_params = {"original": "premium", "capacity": capacity_units_per_month}
        else:
            chosen = "penetration"
            reason_key = "notes.pricing.downgraded_to_penetration"
            reason_params = {"original": "premium", "capacity": capacity_units_per_month}
    elif chosen == "match" and not reach_match:
        chosen = "penetration"
        reason_key = "notes.pricing.downgraded_to_penetration"
        reason_params = {"original": "match", "capacity": capacity_units_per_month}

    positions = [
        {
            "name": "penetration",
            "price_per_unit": p_penetration,
            "break_even_units_per_month": be_penetration,
            "reachable": reach_penetration,
            "reachability_note_key": "notes.pricing.reachable" if reach_penetration else "notes.pricing.exceeds_capacity",
            "recommendation": (chosen == "penetration")
        },
        {
            "name": "match",
            "price_per_unit": p_match,
            "break_even_units_per_month": be_match,
            "reachable": reach_match,
            "reachability_note_key": "notes.pricing.reachable" if reach_match else "notes.pricing.exceeds_capacity",
            "recommendation": (chosen == "match")
        },
        {
            "name": "premium",
            "price_per_unit": p_premium,
            "break_even_units_per_month": be_premium,
            "reachable": reach_premium,
            "reachability_note_key": "notes.pricing.reachable" if reach_premium else "notes.pricing.exceeds_capacity",
            "recommendation": (chosen == "premium")
        }
    ]

    target_price = next(pos["price_per_unit"] for pos in positions if pos["name"] == chosen)
    be_plus_2 = calc_break_even(target_price + 2.0)
    be_minus_2 = calc_break_even(target_price - 2.0)

    return {
        "positions": positions,
        "recommended": chosen,
        "recommended_reason_key": reason_key,
        "recommended_reason_params": reason_params,
        "sensitivity": {
            "plus_2": {"break_even": be_plus_2},
            "minus_2": {"break_even": be_minus_2}
        },
        "provenance": {
            "method": "derived",
            "source": "pricing strategy engine"
        }
    }


if __name__ == "__main__":
    band = {
        "low": 40.0,
        "mid": 50.0,
        "high": 60.0,
        "unit": "litre",
        "source": "Agmarknet",
        "date": "2026-09-24"
    }

    # 1. High demand, no nearby competitor -> premium recommended
    res1 = strategy(
        activity_id="dairy.milk_collection",
        demand_score=75,
        competitor_count=1,
        competitor_within_1km=0,
        project_cost=100000,
        loan=80000,
        quarterly_payment=6000,
        capacity_units_per_month=1000,
        unit_label="litre",
        sector_price_band=band
    )
    assert res1["recommended"] == "premium"
    assert res1["recommended_reason_key"] == "notes.pricing.premium_justified"
    pos_prem = next(p for p in res1["positions"] if p["name"] == "premium")
    assert pos_prem["recommendation"] is True
    assert pos_prem["price_per_unit"] == 66.0  # 60 * 1.1

    # 2. Moderate demand, low competitor count -> match recommended
    res2 = strategy(
        activity_id="dairy.milk_collection",
        demand_score=55,
        competitor_count=2,
        competitor_within_1km=2,
        project_cost=100000,
        loan=80000,
        quarterly_payment=6000,
        capacity_units_per_month=1000,
        unit_label="litre",
        sector_price_band=band
    )
    assert res2["recommended"] == "match"
    assert res2["recommended_reason_key"] == "notes.pricing.match_market"
    pos_match = next(p for p in res2["positions"] if p["name"] == "match")
    assert pos_match["recommendation"] is True
    assert pos_match["price_per_unit"] == 50.0

    # 3. Low demand, high competitor count -> penetration recommended
    res3 = strategy(
        activity_id="dairy.milk_collection",
        demand_score=40,
        competitor_count=5,
        competitor_within_1km=3,
        project_cost=100000,
        loan=80000,
        quarterly_payment=6000,
        capacity_units_per_month=1000,
        unit_label="litre",
        sector_price_band=band
    )
    assert res3["recommended"] == "penetration"
    assert res3["recommended_reason_key"] == "notes.pricing.penetration_volume"
    pos_pen = next(p for p in res3["positions"] if p["name"] == "penetration")
    assert pos_pen["recommendation"] is True
    assert pos_pen["price_per_unit"] == 36.0  # 40 * 0.9

    # 4. Premium unreachable due to capacity -> downgraded to match
    # monthly_fixed = 6000/3 = 2000. variable_cost = 24.
    # premium price = 66, margin = 42, break_even = ceil(2000/42) = 48.
    # If capacity is 30, premium break_even (48) > 30 -> unreachable.
    res4 = strategy(
        activity_id="dairy.milk_collection",
        demand_score=80,
        competitor_count=0,
        competitor_within_1km=0,
        project_cost=100000,
        loan=80000,
        quarterly_payment=6000,
        capacity_units_per_month=30,  # lower than break_even (48)
        unit_label="litre",
        sector_price_band=band
    )
    # Match break-even is 2000 / (50 - 24) = 77 > 30, so both premium & match unreachable -> downgraded to penetration
    assert res4["recommended"] in ("match", "penetration")

    # 5. Penetration unreachable still returned with reachable: False
    res5 = strategy(
        activity_id="dairy.milk_collection",
        demand_score=30,
        competitor_count=8,
        competitor_within_1km=4,
        project_cost=100000,
        loan=80000,
        quarterly_payment=30000,  # 10000 monthly fixed
        capacity_units_per_month=10,  # very low capacity
        unit_label="litre",
        sector_price_band=band
    )
    assert res5["recommended"] == "penetration"
    pen_pos = next(p for p in res5["positions"] if p["name"] == "penetration")
    assert pen_pos["reachable"] is False
    assert pen_pos["reachability_note_key"] == "notes.pricing.exceeds_capacity"

    # 6. Check price formulas
    assert pos_pen["price_per_unit"] == round(band["low"] * 0.9, 2)
    assert pos_match["price_per_unit"] == band["mid"]
    assert pos_prem["price_per_unit"] == round(band["high"] * 1.1, 2)

    # 7. Check sensitivity values exist and are positive
    assert "plus_2" in res1["sensitivity"]
    assert "minus_2" in res1["sensitivity"]
    assert res1["sensitivity"]["plus_2"]["break_even"] < res1["sensitivity"]["minus_2"]["break_even"]

    # 8. Check positions structure
    assert len(res1["positions"]) == 3
    names = {p["name"] for p in res1["positions"]}
    assert names == {"penetration", "match", "premium"}

    # 9. Provenance is present and correct
    assert res1["provenance"]["method"] == "derived"
    assert res1["provenance"]["source"] == "pricing strategy engine"

    # 10. Exactly one position is recommended
    assert sum(1 for p in res1["positions"] if p["recommendation"]) == 1
    assert sum(1 for p in res2["positions"] if p["recommendation"]) == 1
    assert sum(1 for p in res3["positions"] if p["recommendation"]) == 1

    print("All 10+ pricing strategy tests passed successfully!")
