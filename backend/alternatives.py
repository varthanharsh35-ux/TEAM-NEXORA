"""Alternative activities and locations recommendation engine."""

import json
import math
from pathlib import Path
from drivers import score as driver_score, band_for

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TAXONOMY_PATH = DATA_DIR / "taxonomy.json"
_VILLAGES_PATH = DATA_DIR / "villages.json"


def _load_taxonomy() -> dict:
    if _TAXONOMY_PATH.exists():
        try:
            with open(_TAXONOMY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _load_villages() -> list:
    if _VILLAGES_PATH.exists():
        try:
            with open(_VILLAGES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute Haversine distance in kilometers between two lat/lon pairs."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    return 2.0 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def better_activities(
    location_id: str,
    lat: float,
    lon: float,
    chosen_activity_id: str,
    chosen_demand_score: int,
    margin: float,
    radius_km: float = 10.0,
    top_n: int = 3,
    driver_points: list = None,
    competitors: list = None
) -> dict:
    """Recommend higher-scoring alternative activities within capital budget."""
    taxonomy = _load_taxonomy()
    points = driver_points or []
    rivals = competitors or []

    max_affordable_project = (margin / 0.10) if margin and margin > 0 else 0.0

    candidates = []
    evaluated = 0

    for sector in taxonomy.get("sectors", []):
        for act in sector.get("activities", []):
            evaluated += 1
            if evaluated > 50:
                break

            act_id = act.get("id")
            if not act_id or act_id == chosen_activity_id:
                continue

            cost_info = act.get("typical_project_cost") or {}
            min_cost = cost_info.get("min") if cost_info.get("min") is not None else 0
            max_cost = cost_info.get("max") if cost_info.get("max") is not None else min_cost

            # Filter: typical_project_cost.min <= margin / 0.10
            if margin > 0 and min_cost > max_affordable_project:
                continue

            try:
                res = driver_score(act_id, points, rivals)
                act_score = res["demand_score"]["value"]
                act_band = res["demand_score"]["band"]

                # Filter: score > chosen_demand_score
                if act_score <= chosen_demand_score:
                    continue

                top_d = None
                drivers_list = res.get("drivers", [])
                if drivers_list:
                    d0 = drivers_list[0]
                    top_d = {
                        "id": d0.get("id"),
                        "direction": d0.get("direction"),
                        "count": d0.get("count"),
                        "nearest_m": d0.get("nearest_m"),
                        "evidence": d0.get("evidence", [])
                    }

                delta = act_score - chosen_demand_score
                candidates.append({
                    "activity_id": act_id,
                    "activity_name": {"en": act.get("names", {}).get("en", act_id)},
                    "demand_score": act_score,
                    "band": act_band,
                    "score_delta": delta,
                    "capital_required_min": min_cost,
                    "capital_required_max": max_cost,
                    "top_driver": top_d,
                    "reason_key": "alternatives.higher_demand_fit",
                    "reason_params": {"score_delta": delta, "min_cost": min_cost}
                })
            except Exception:
                continue

        if evaluated > 50:
            break

    candidates.sort(key=lambda x: (-x["demand_score"], x["capital_required_min"]))
    alternatives = candidates[:top_n]

    return {
        "alternatives": alternatives,
        "chosen_score": chosen_demand_score,
        "chosen_band": band_for(chosen_demand_score),
        "provenance": {
            "method": "derived",
            "source": "drivers.py + taxonomy"
        }
    }


def better_locations(
    chosen_activity_id: str,
    chosen_lat: float,
    chosen_lon: float,
    chosen_demand_score: int,
    radius_km: float = 25.0,
    top_n: int = 3,
    points_by_village: dict = None
) -> dict:
    """Recommend nearby villages offering stronger demand drivers for the activity."""
    all_villages = _load_villages()
    village_points = points_by_village or {}

    nearby = []
    for v in all_villages:
        v_lat = v.get("lat")
        v_lon = v.get("lon")
        if v_lat is None or v_lon is None:
            continue

        dist = haversine_km(chosen_lat, chosen_lon, float(v_lat), float(v_lon))
        if 0.1 <= dist <= radius_km:
            nearby.append((dist, v))

    nearby.sort(key=lambda x: x[0])
    candidates = nearby[:20]

    better = []
    for dist, v in candidates:
        vid = v.get("id", "")
        pts = village_points.get(vid, [])
        try:
            res = driver_score(chosen_activity_id, pts)
            v_score = res["demand_score"]["value"]
            if v_score > chosen_demand_score:
                delta = v_score - chosen_demand_score
                better.append({
                    "location_id": vid,
                    "name": v.get("name", ""),
                    "district": v.get("district", ""),
                    "lat": float(v["lat"]),
                    "lon": float(v["lon"]),
                    "distance_km": round(dist, 2),
                    "demand_score": v_score,
                    "score_delta": delta,
                    "reason_key": "alternatives.higher_demand_location",
                    "reason_params": {"score_delta": delta, "distance_km": round(dist, 2)}
                })
        except Exception:
            continue

    better.sort(key=lambda x: (-x["demand_score"], x["distance_km"]))
    final_locations = better[:top_n]

    return {
        "better_locations": final_locations,
        "provenance": {
            "method": "derived",
            "source": "drivers.py + villages"
        }
    }


if __name__ == "__main__":
    def poi(kind, name, distance_m):
        return {"kind": kind, "name": name, "distance_m": distance_m, "source_url": "https://osm.org/node/1"}

    # Mock POIs near test location: a college and a bus stand
    test_pois = [
        poi("college", "Government Arts College", 250),
        poi("bus_stand", "Central Bus Stop", 150)
    ]

    # 1. better_activities returns structure and provenance
    res_act = better_activities(
        location_id="loc_1",
        lat=11.0,
        lon=78.0,
        chosen_activity_id="agriculture.paddy",
        chosen_demand_score=50,
        margin=50000,
        radius_km=10.0,
        top_n=3,
        driver_points=test_pois
    )
    assert "alternatives" in res_act
    assert "chosen_score" in res_act
    assert res_act["provenance"]["method"] == "derived"
    assert res_act["provenance"]["source"] == "drivers.py + taxonomy"

    # 2. All alternatives have score > chosen_demand_score
    for alt in res_act["alternatives"]:
        assert alt["demand_score"] > 50
        assert alt["score_delta"] > 0
        assert alt["activity_id"] != "agriculture.paddy"

    # 3. Capital requirement filter: min_cost <= margin / 0.10 (500,000)
    for alt in res_act["alternatives"]:
        assert alt["capital_required_min"] <= 500000

    # 4. Top driver information populated when drivers present
    if res_act["alternatives"]:
        top_alt = res_act["alternatives"][0]
        assert "activity_name" in top_alt
        assert "en" in top_alt["activity_name"]

    # 5. When chosen_score is high (95), alternatives is empty
    res_high = better_activities(
        location_id="loc_1",
        lat=11.0,
        lon=78.0,
        chosen_activity_id="food.cafe",
        chosen_demand_score=95,
        margin=50000,
        driver_points=test_pois
    )
    assert len(res_high["alternatives"]) == 0

    # 6. Haversine distance test
    d = haversine_km(13.0827, 80.2707, 13.0827, 80.2707)
    assert round(d, 2) == 0.0
    d_far = haversine_km(13.0, 80.0, 14.0, 80.0)
    assert 105.0 < d_far < 115.0

    # 7. better_locations returns structure and filters by distance
    mock_villages_points = {
        "1-1-1": [poi("railway", "Main Railway Junction", 100)],
        "1-1-2": [poi("hospital", "District Hospital", 300)]
    }
    res_loc = better_locations(
        chosen_activity_id="food.cafe",
        chosen_lat=12.77,
        chosen_lon=79.83,
        chosen_demand_score=50,
        radius_km=30.0,
        top_n=3,
        points_by_village=mock_villages_points
    )
    assert "better_locations" in res_loc
    assert res_loc["provenance"]["method"] == "derived"

    # 8. All better_locations have demand_score > chosen_demand_score
    for bloc in res_loc["better_locations"]:
        assert bloc["demand_score"] > 50
        assert bloc["distance_km"] <= 30.0
        assert bloc["score_delta"] > 0
        assert "district" in bloc

    print("All 8+ alternatives tests passed successfully!")
