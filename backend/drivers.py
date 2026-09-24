"""Local demand drivers (docs/TASKS.md Task 2.1, docs/PERSONALIZATION.md).

The report used to say "avoid dependency on a single buyer" -- advice true of
every business on earth. This module produces the local facts that make advice
specific: real named places near the user that raise or lower demand for their
particular activity, weighted by how far away they are.

Nothing here invents a place. A driver with no named evidence is never emitted,
because "there is a college nearby" is worth nothing if we cannot say which one.
"""

import json
import math
import re
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


@lru_cache(maxsize=1)
def config():
    return json.loads((DATA / "drivers.json").read_text(encoding="utf-8"))


def sector_of(activity):
    """'food.cafe' -> 'food'. Weights are held per sector, not per activity."""
    return (activity or "").split(".")[0]


def weights_for(activity):
    return config()["weights"].get(sector_of(activity), {})


SELECTOR = re.compile(r'\["([^"\]]+)"(?:(~|!=|=)"([^"\]]*)")?(?:,(i))?\]')


def matches(tags, selector):
    """Evaluate one declarative selector from drivers.json against OSM tags.

    Only the selector vocabulary used in that file is supported; anything else
    raises rather than silently matching nothing.
    """
    parts = list(SELECTOR.finditer(selector))
    if not parts or "".join(p.group() for p in parts) != selector:
        raise ValueError(f"unsupported_selector: {selector}")
    for part in parts:
        name, operator, expected, insensitive = part.groups()
        actual = tags.get(name)
        if actual is None:
            return False
        if operator == "=" and actual != expected:
            return False
        if operator == "!=" and actual == expected:
            return False
        if operator == "~":
            flags = re.IGNORECASE if insensitive else 0
            if not isinstance(actual, str):
                return False
            # Unanchored patterns are what produced the blood_bank bug, so the
            # whole value must match unless the pattern itself allows more.
            if re.fullmatch(expected, actual, flags) is None and re.search(expected, actual, flags) is None:
                return False
    return True


def classify(tags):
    """Return the driver kind for a POI, or None if it is not a driver."""
    if not isinstance(tags, dict):
        return None
    for kind, spec in config()["kinds"].items():
        for selector in spec["selectors"]:
            if matches(tags, selector):
                return kind
    return None


def all_selectors():
    """Every driver selector, for inclusion in the Overpass query."""
    return [s for spec in config()["kinds"].values() for s in spec["selectors"]]


def decay(weight, distance_m, kind):
    """Half-life falloff: a college 600 m away counts half as much as one next door."""
    half_life = config()["half_life_m"][config()["kinds"][kind]["class"]]
    return weight * 0.5 ** (distance_m / half_life)


def band_for(score):
    for band in config()["bands"]:
        if band["min"] <= score <= band["max"]:
            return band["id"]
    return "fair"


def score(activity, driver_points, competitors=()):
    """Turn observed POIs into weighted drivers and a 0-100 demand score.

    `driver_points` are dicts with kind, name, distance_m and source_url.
    `competitors` are the mapped competitors, which suppress demand themselves.
    """
    settings = config()
    weights = weights_for(activity)
    grouped = {}

    for point in driver_points:
        kind = point.get("kind")
        weight = weights.get(kind)
        if not weight or not point.get("name"):
            # No weight for this sector, or nothing we can name as evidence.
            continue
        grouped.setdefault(kind, []).append(point)

    drivers = []
    for kind, points in grouped.items():
        base = weights[kind]
        effect = sum(decay(base, p["distance_m"], kind) for p in points)
        nearest = min(points, key=lambda p: p["distance_m"])
        evidence = [
            {"name": p["name"], "distance_m": round(p["distance_m"]), "source_url": p.get("source_url")}
            for p in sorted(points, key=lambda p: p["distance_m"])[:3]
        ]
        drivers.append({
            "id": kind,
            "direction": "boost" if base > 0 else "suppress",
            "weight": round(effect, 3),
            "count": len(points),
            "nearest_m": round(nearest["distance_m"]),
            "emoji": settings["kinds"][kind]["emoji"],
            "evidence": evidence,
            "reason_key": f"drivers.{kind}.{'boost' if base > 0 else 'suppress'}",
            "reason_params": {"count": len(points), "nearest_m": round(nearest["distance_m"])},
        })

    # Existing competitors suppress demand on their own. Direct competitors count
    # fully, partial substitutes at 40 percent.
    direct = [c for c in competitors if c.get("match") == "direct"]
    adjacent = [c for c in competitors if c.get("match") == "adjacent"]
    if direct or adjacent:
        effect = sum(decay(-0.18, c["distance_m"], "big_retail") for c in direct)
        effect += sum(decay(-0.072, c["distance_m"], "big_retail") for c in adjacent)
        nearest = min(direct + adjacent, key=lambda c: c["distance_m"])
        named = [c for c in sorted(direct + adjacent, key=lambda c: c["distance_m"]) if c.get("name")][:3]
        drivers.append({
            "id": "competitor_density",
            "direction": "suppress",
            "weight": round(effect, 3),
            "count": len(direct) + len(adjacent),
            "nearest_m": round(nearest["distance_m"]),
            "emoji": "\U0001f3ea",
            "evidence": [
                {"name": c["name"], "distance_m": c["distance_m"], "source_url": c.get("source_url")}
                for c in named
            ],
            "reason_key": "drivers.competitor_density.suppress",
            "reason_params": {"count": len(direct) + len(adjacent), "nearest_m": round(nearest["distance_m"])},
        })

    caps = settings["caps"]
    boost = min(caps["boost"], sum(d["weight"] for d in drivers if d["weight"] > 0))
    suppress = max(caps["suppress"], sum(d["weight"] for d in drivers if d["weight"] < 0))
    total = boost + suppress
    value = max(0, min(100, round(50 * (1 + total))))

    drivers.sort(key=lambda d: -abs(d["weight"]))
    return {
        "drivers": drivers,
        "demand_score": {
            "value": value,
            "band": band_for(value),
            "scale": "0-100",
            "components": {"boost": round(boost, 3), "suppress": round(suppress, 3)},
            "provenance": {
                "method": "derived",
                "source": "OpenStreetMap places weighted by authored priors",
                "weights_version": settings["version"],
            },
        },
    }
