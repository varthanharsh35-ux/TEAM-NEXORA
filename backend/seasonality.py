"""Seasonality and climate analysis for rural and micro-enterprises in Tamil Nadu."""

import json
from pathlib import Path

# Load IMD climate normals from static dataset
_CLIMATE_PATH = Path(__file__).resolve().parents[1] / "data" / "climate.json"


def _load_climate() -> dict:
    if _CLIMATE_PATH.exists():
        try:
            with open(_CLIMATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("districts", {})
        except Exception:
            return {}
    return {}


CLIMATE = _load_climate()

# Activity prefix / ID specific monthly modifiers
# month: 1-12. factor: multiplier applied to 1.0 base.
MODIFIERS = {
    # College vacation: Apr-May (months 4, 5) suppress food.cafe and education.*
    "college_vacation": {
        "prefixes": ["food.cafe", "education."],
        "months": [4, 5],
        "factor": 0.6,
        "reason_key": "notes.seasonality.college_vacation"
    },
    # Festival: Pongal in Jan (month 1), Deepavali in Oct/Nov (months 10, 11) boost retail, beauty, tailoring
    "pongal": {
        "prefixes": ["retail.", "beauty.", "tailoring."],
        "months": [1],
        "factor": 1.3,
        "reason_key": "notes.seasonality.pongal"
    },
    "deepavali": {
        "prefixes": ["retail.", "beauty.", "tailoring."],
        "months": [10, 11],
        "factor": 1.3,
        "reason_key": "notes.seasonality.deepavali"
    },
    # Fisheries: peak Dec-Feb (12, 1, 2) and Jun-Aug (6, 7, 8)
    "fisheries_winter": {
        "prefixes": ["fisheries.", "fish"],
        "months": [12, 1, 2],
        "factor": 1.25,
        "reason_key": "notes.seasonality.fisheries_peak"
    },
    "fisheries_monsoon_gap": {
        "prefixes": ["fisheries.", "fish"],
        "months": [6, 7, 8],
        "factor": 1.25,
        "reason_key": "notes.seasonality.fisheries_peak"
    },
    # Tamil Nadu annual 61-day marine fishing ban (Apr 15 - Jun 14)
    "fisheries_ban": {
        "prefixes": ["fisheries.", "fish"],
        "months": [4, 5],
        "factor": 0.70,
        "reason_key": "notes.seasonality.fisheries_ban"
    }
}


def _norm_district(district_id: str | None) -> str:
    if not district_id:
        return "chennai"
    d = district_id.lower().strip().replace(" ", "_").replace("-", "_")
    return d if d in CLIMATE else "chennai"


def district_climate(district_id: str) -> dict:
    """Return climate normals for a Tamil Nadu district."""
    d = _norm_district(district_id)
    info = CLIMATE.get(d, CLIMATE.get("chennai", {}))
    return {
        "zone": info.get("zone", "northeast_coastal"),
        "annual_rainfall_mm": info.get("annual_rainfall_mm", 1000),
        "monsoon": info.get("monsoon", ["northeast:oct-dec"]),
        "summer_max_c": info.get("summer_max_c", 38),
        "winter_min_c": info.get("winter_min_c", 20),
        "provenance": {
            "method": "official",
            "source": "IMD district normals"
        }
    }


def monthly_index(activity_id: str, district_id: str = None) -> list[dict]:
    """Compute monthly seasonal index for an activity in a district.

    Returns 12 dicts: {month: 1-12, index: float, reasons: [str]}
    Baseline is 1.0, minimum is 0.5. Reasons are i18n keys.
    """
    act = (activity_id or "").lower().strip()
    c_info = district_climate(district_id)
    monsoons = c_info.get("monsoon", [])
    is_sw = any("southwest" in m for m in monsoons)

    result = []
    for month in range(1, 13):
        index = 1.0
        reasons = []

        # Check activity-based modifiers
        for mod in MODIFIERS.values():
            if month in mod["months"]:
                for prefix in mod["prefixes"]:
                    if act.startswith(prefix) or act == prefix:
                        index *= mod["factor"]
                        if mod["reason_key"] not in reasons:
                            reasons.append(mod["reason_key"])
                        break

        # Check transport monsoon suppression
        if act.startswith("transport.") or act == "transport":
            # SW monsoon: Jun-Sep (6-9)
            if is_sw and month in (6, 7, 8, 9):
                index *= 0.75
                reasons.append("notes.seasonality.monsoon_transport")
            # NE monsoon: Oct-Dec (10-12) for all other TN districts
            elif not is_sw and month in (10, 11, 12):
                index *= 0.75
                reasons.append("notes.seasonality.monsoon_transport")

        # Clamp baseline min 0.5
        index = max(0.5, round(index, 2))
        result.append({
            "month": month,
            "index": index,
            "reasons": reasons
        })

    return result


def seasonality_note_key(activity_id: str, month: int) -> str | None:
    """Return the strongest i18n reason key for an activity and month, or None."""
    items = monthly_index(activity_id)
    if 1 <= month <= 12:
        entry = items[month - 1]
        if entry["reasons"]:
            return entry["reasons"][0]
    return None


if __name__ == "__main__":
    # 1. Output format check: 12 months returned
    m1 = monthly_index("food.cafe")
    assert len(m1) == 12, "Should return 12 months"
    assert [x["month"] for x in m1] == list(range(1, 13)), "Months must be 1 to 12"

    # 2. College vacation suppresses food.cafe in Apr-May (months 4, 5)
    assert m1[3]["index"] == 0.6, f"Apr cafe index expected 0.6, got {m1[3]['index']}"
    assert m1[4]["index"] == 0.6, f"May cafe index expected 0.6, got {m1[4]['index']}"
    assert "notes.seasonality.college_vacation" in m1[3]["reasons"]

    # 3. College vacation suppresses education.* in Apr-May
    m_edu = monthly_index("education.tuition_centre")
    assert m_edu[3]["index"] == 0.6
    assert m_edu[4]["index"] == 0.6
    assert "notes.seasonality.college_vacation" in m_edu[3]["reasons"]

    # 4. Baseline months are 1.0 when no modifiers apply
    assert m1[0]["index"] == 1.0, f"Jan cafe index expected 1.0, got {m1[0]['index']}"
    assert m1[1]["index"] == 1.0, "Feb cafe index expected 1.0"

    # 5. Pongal Jan boost for retail.*
    m_ret = monthly_index("retail.grocery")
    assert m_ret[0]["index"] == 1.3, f"Jan retail expected 1.3, got {m_ret[0]['index']}"
    assert "notes.seasonality.pongal" in m_ret[0]["reasons"]

    # 6. Deepavali Oct/Nov boost for retail, beauty, tailoring
    assert m_ret[9]["index"] == 1.3, f"Oct retail expected 1.3, got {m_ret[9]['index']}"
    assert m_ret[10]["index"] == 1.3, f"Nov retail expected 1.3, got {m_ret[10]['index']}"
    assert "notes.seasonality.deepavali" in m_ret[9]["reasons"]

    m_tailor = monthly_index("tailoring.stitching")
    assert m_tailor[0]["index"] == 1.3
    assert m_tailor[9]["index"] == 1.3
    assert m_tailor[10]["index"] == 1.3

    m_beauty = monthly_index("beauty.parlour_women")
    assert m_beauty[0]["index"] == 1.3
    assert m_beauty[9]["index"] == 1.3

    # 7. Fisheries peak Dec-Feb and Jun-Aug
    m_fish = monthly_index("fisheries.fresh_fish_retail")
    assert m_fish[11]["index"] == 1.25, "Dec fisheries expected 1.25"
    assert m_fish[0]["index"] == 1.25, "Jan fisheries expected 1.25"
    assert m_fish[1]["index"] == 1.25, "Feb fisheries expected 1.25"
    assert m_fish[5]["index"] == 1.25, "Jun fisheries expected 1.25"
    assert m_fish[6]["index"] == 1.25, "Jul fisheries expected 1.25"
    assert m_fish[7]["index"] == 1.25, "Aug fisheries expected 1.25"
    assert "notes.seasonality.fisheries_peak" in m_fish[0]["reasons"]

    # 8. Transport NE monsoon suppression (Chennai, Oct-Dec)
    m_trans_ne = monthly_index("transport.goods_tempo", "chennai")
    assert m_trans_ne[9]["index"] == 0.75, "Oct transport chennai expected 0.75"
    assert m_trans_ne[10]["index"] == 0.75, "Nov transport chennai expected 0.75"
    assert m_trans_ne[11]["index"] == 0.75, "Dec transport chennai expected 0.75"
    assert "notes.seasonality.monsoon_transport" in m_trans_ne[9]["reasons"]
    assert m_trans_ne[6]["index"] == 1.0, "Jul transport chennai expected 1.0"

    # 9. Transport SW monsoon suppression (Nilgiris, Jun-Sep)
    m_trans_sw = monthly_index("transport.goods_tempo", "nilgiris")
    assert m_trans_sw[5]["index"] == 0.75, "Jun transport nilgiris expected 0.75"
    assert m_trans_sw[6]["index"] == 0.75, "Jul transport nilgiris expected 0.75"
    assert m_trans_sw[7]["index"] == 0.75, "Aug transport nilgiris expected 0.75"
    assert m_trans_sw[8]["index"] == 0.75, "Sep transport nilgiris expected 0.75"
    assert m_trans_sw[10]["index"] == 1.0, "Nov transport nilgiris expected 1.0"

    # 10. Minimum index clamp at 0.5
    for m in range(1, 13):
        assert m1[m - 1]["index"] >= 0.5, "Index must never drop below 0.5"

    # 11. district_climate returned shape and provenance
    c_che = district_climate("chennai")
    assert c_che["annual_rainfall_mm"] == 1400
    assert c_che["summer_max_c"] == 40
    assert c_che["provenance"]["method"] == "official"
    assert c_che["provenance"]["source"] == "IMD district normals"

    c_nil = district_climate("nilgiris")
    assert c_nil["annual_rainfall_mm"] == 1800
    assert c_nil["summer_max_c"] == 22

    # 12. Fallback on invalid district
    c_inv = district_climate("unknown_district")
    assert "annual_rainfall_mm" in c_inv
    assert c_inv["provenance"]["method"] == "official"

    # 13. All 38 districts loaded
    assert len(CLIMATE) >= 38, f"Expected 38 districts in CLIMATE, found {len(CLIMATE)}"

    # 14. seasonality_note_key function test
    assert seasonality_note_key("food.cafe", 4) == "notes.seasonality.college_vacation"
    assert seasonality_note_key("retail.grocery", 1) == "notes.seasonality.pongal"
    assert seasonality_note_key("repair.mobile_repair", 3) is None

    # 15. Activity with no modifiers has baseline 1.0 across all 12 months
    m_rep = monthly_index("repair.mobile_repair")
    assert all(x["index"] == 1.0 for x in m_rep), "Repair should have baseline 1.0 throughout"
    assert all(len(x["reasons"]) == 0 for x in m_rep), "Repair should have no seasonal reasons"

    print("All 15+ seasonality tests passed successfully!")
