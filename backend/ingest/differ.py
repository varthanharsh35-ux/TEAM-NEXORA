"""Catalogue differ enforcing safety thresholds and the two-crawl withdrawal rule."""

import copy
from datetime import date


class PublishBlocked(Exception):
    """Raised when an ingestion change is too drastic to publish automatically."""
    pass


def diff_schemes(old_list: list, new_list: list, id_field: str = "id") -> dict:
    """Compare two snapshots of schemes and categorize changes.

    Raises PublishBlocked if 40% or more existing schemes would be removed.
    """
    old_map = {item[id_field]: item for item in old_list if id_field in item}
    new_map = {item[id_field]: item for item in new_list if id_field in item}

    added = []
    changed = []
    removed = []
    unchanged = []

    for sid, new_item in new_map.items():
        if sid not in old_map:
            added.append(new_item)
        elif old_map[sid] != new_item:
            changed.append({"old": old_map[sid], "new": new_item})
        else:
            unchanged.append(new_item)

    for sid, old_item in old_map.items():
        if sid not in new_map:
            removed.append(old_item)

    if old_list and (len(removed) / len(old_list)) >= 0.4:
        raise PublishBlocked(
            f"Removal threshold exceeded: {len(removed)}/{len(old_list)} "
            f"({len(removed) / len(old_list):.1%}) schemes missing"
        )

    return {
        "added": added,
        "changed": changed,
        "removed": removed,
        "unchanged": unchanged
    }


def confirm_withdrawn(removed_candidates: dict | set | list, currently_removed: list) -> list:
    """Two-crawl rule: Confirm withdrawal only if missing for two consecutive crawls."""
    prev_ids = set(removed_candidates.keys()) if isinstance(removed_candidates, dict) else set(removed_candidates)
    curr_ids = set(item["id"] if isinstance(item, dict) and "id" in item else item for item in currently_removed)
    return sorted(list(prev_ids.intersection(curr_ids)))


def apply_withdrawn(catalog: dict, confirmed_ids: list) -> dict:
    """Mark confirmed withdrawn schemes with withdrawn_on timestamp. NEVER delete records."""
    cat = copy.deepcopy(catalog)
    today_str = date.today().isoformat()
    c_set = set(confirmed_ids)

    for scheme in cat.get("schemes", []):
        if scheme.get("id") in c_set and not scheme.get("withdrawn_on"):
            scheme["withdrawn_on"] = today_str
            scheme["status"] = "withdrawn"
            reasons = set(scheme.get("reasons", []))
            reasons.add("reasons.scheme_withdrawn")
            scheme["reasons"] = sorted(reasons)

    return cat


if __name__ == "__main__":
    old = [
        {"id": "s1", "name": "Scheme 1", "rate": 6.0},
        {"id": "s2", "name": "Scheme 2", "rate": 7.0},
        {"id": "s3", "name": "Scheme 3", "rate": 8.0}
    ]

    # 1. Normal diff: 1 added, 1 changed, 1 unchanged
    new = [
        {"id": "s1", "name": "Scheme 1", "rate": 6.5},  # changed
        {"id": "s2", "name": "Scheme 2", "rate": 7.0},  # unchanged
        {"id": "s4", "name": "Scheme 4", "rate": 5.0}   # added
    ]
    res = diff_schemes(old, new)
    assert len(res["added"]) == 1
    assert res["added"][0]["id"] == "s4"
    assert len(res["changed"]) == 1
    assert res["changed"][0]["new"]["id"] == "s1"
    assert len(res["removed"]) == 1
    assert res["removed"][0]["id"] == "s3"
    assert len(res["unchanged"]) == 1
    assert res["unchanged"][0]["id"] == "s2"

    # 2. PublishBlocked raised when >= 40% removed
    new_catastrophic = [
        {"id": "s1", "name": "Scheme 1", "rate": 6.0}
    ]
    # Removed s2, s3 (2/3 = 66.7% >= 40%)
    try:
        diff_schemes(old, new_catastrophic)
        assert False, "Should raise PublishBlocked"
    except PublishBlocked as e:
        assert "threshold exceeded" in str(e)

    # 3. Two-crawl rule confirms only consecutive removals
    prev_missing = {"s3": "2026-09-01", "s9": "2026-09-01"}
    curr_missing = [{"id": "s3"}, {"id": "s4"}]
    confirmed = confirm_withdrawn(prev_missing, curr_missing)
    assert confirmed == ["s3"]  # s4 not in prev, s9 not in curr

    # 4. apply_withdrawn sets withdrawn_on and does NOT delete
    cat_mock = {"schemes": copy.deepcopy(old)}
    updated_cat = apply_withdrawn(cat_mock, ["s3"])
    assert len(updated_cat["schemes"]) == 3, "Schemes must NEVER be deleted"
    s3_item = next(s for s in updated_cat["schemes"] if s["id"] == "s3")
    assert s3_item["withdrawn_on"] == date.today().isoformat()
    assert s3_item["status"] == "withdrawn"
    assert "reasons.scheme_withdrawn" in s3_item["reasons"]

    # 5. Non-withdrawn schemes untouched
    s1_item = next(s for s in updated_cat["schemes"] if s["id"] == "s1")
    assert s1_item.get("withdrawn_on") is None

    # 6. Two-crawl with set input
    assert confirm_withdrawn({"s1", "s2"}, ["s2", "s3"]) == ["s2"]

    print("All 6+ differ tests passed successfully!")
