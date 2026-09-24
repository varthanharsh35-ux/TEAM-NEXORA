"""Attach coordinates to the Tamil Nadu gazetteer (docs/TASKS.md Task 1.1).

The TNRD directory in data/villages.json lists 12,620 villages as
{id, name, block, district} with no coordinates, so nothing can be placed on a
map and every lookup had to hit a live geocoder behind a global rate limit.
Failures then surfaced to users as "outside Tamil Nadu".

This script fetches every named place node in Tamil Nadu from OpenStreetMap,
one district at a time, and matches them against the directory. It also keeps
the OSM places the directory does not contain at all -- urban localities such as
Saravanampatti, which is a Coimbatore suburb rather than a TNRD rural village
and was therefore missing entirely.

Stages (both resumable, safe to re-run):

    python scripts/geocode_gazetteer.py fetch    # 38 Overpass queries -> data/raw/osm_places/
    python scripts/geocode_gazetteer.py build    # match + write gazetteer files
    python scripts/geocode_gazetteer.py report   # coverage summary

Data (c) OpenStreetMap contributors, ODbL 1.0.
"""

import argparse
import difflib
import json
import sys
import time
import unicodedata
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = DATA / "raw" / "osm_places"
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
AGENT = "GramSahayak-SIH-gazetteer/1.0 (student project; contact via repository)"
PAUSE_S = 5
PLACE_KINDS = "city|town|village|hamlet|suburb|neighbourhood|isolated_dwelling|locality"


def norm(text):
    """Casefold, strip accents and punctuation. Keeps Tamil and Devanagari letters."""
    decomposed = unicodedata.normalize("NFKD", text).casefold()
    return "".join(c for c in decomposed if c.isalnum())


# Tamil romanisation is not standardised: the same village is written Arumbuliyur
# or Arumpuliyur, Edayambudur or Edayampudur. Voiced and unvoiced stops alternate
# freely (b/p, d/t, g/k, j/s), aspirates are optional, consonants double or not,
# and long vowels are spelled with doubled letters or macrons. Folding these
# equivalences turns near-misses into exact matches without loosening the fuzzy
# threshold, which would instead let genuinely different names through.
DIGRAPHS = [
    ("zh", "l"), ("th", "t"), ("dh", "t"), ("ph", "p"), ("bh", "p"),
    ("gh", "k"), ("kh", "k"), ("ch", "c"), ("sh", "s"),
    ("oo", "u"), ("ee", "i"), ("aa", "a"), ("ai", "y"), ("ay", "y"),
]
LETTERS = str.maketrans({"b": "p", "d": "t", "g": "k", "j": "c", "z": "s", "w": "v"})


def fold(text):
    """Normalised key with Tamil romanisation variants collapsed."""
    key = norm(text)
    for src, dst in DIGRAPHS:
        key = key.replace(src, dst)
    key = key.translate(LETTERS)
    out = []
    for char in key:
        if not out or out[-1] != char:
            out.append(char)
    return "".join(out)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")


# --------------------------------------------------------------------------- fetch


def overpass(query, timeout=300, attempts=4):
    """Query Overpass, rotating mirrors and backing off on 429 and 504.

    The public instance rate-limits and times out on district-sized queries, so
    a single pass leaves gaps. Rotating across mirrors with exponential backoff
    spreads the load and lets a re-run fill them in.
    """
    last = None
    for attempt in range(attempts):
        url = MIRRORS[attempt % len(MIRRORS)]
        try:
            response = httpx.post(
                url, data={"data": query}, timeout=timeout, headers={"User-Agent": AGENT}
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:  # noqa: BLE001 - retried below
            last = error
            if attempt < attempts - 1:
                wait = PAUSE_S * 2 ** attempt
                print(f"      retry in {wait}s ({type(error).__name__})", file=sys.stderr)
                time.sleep(wait)
    raise last


def osm_district_names():
    """The 38 admin_level=5 relations inside Tamil Nadu."""
    query = (
        '[out:json][timeout:300];'
        'area["ISO3166-2"="IN-TN"][admin_level=4]->.tn;'
        'rel["admin_level"="5"]["name"](area.tn);'
        "out tags;"
    )
    return sorted(e["tags"]["name"] for e in overpass(query)["elements"])


def crosswalk(ours, osm_names):
    """Map each directory district id to its OSM relation name.

    Names agree for 37 of 38 districts; the remainder differ only by
    transliteration, so a fuzzy fallback resolves it without naming any
    district in code (RULES.md rule 3).
    """
    index = {norm(n): n for n in osm_names}
    pairs = {}
    for district in ours:
        candidates = [district["id"], *district["names"].values(), *district.get("aliases", [])]
        hit = next((index[norm(c)] for c in candidates if norm(c) in index), None)
        if hit is None:
            close = difflib.get_close_matches(norm(district["id"]), list(index), 1, 0.6)
            hit = index[close[0]] if close else None
        if hit is None:
            print(f"  ! no OSM district for {district['id']!r}", file=sys.stderr)
            continue
        pairs[district["id"]] = hit
    return pairs


def fetch(force=False):
    districts = read_json(DATA / "districts.json")
    pairs = crosswalk(districts, osm_district_names())
    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"fetching place nodes for {len(pairs)} districts into {CACHE.relative_to(ROOT)}")

    for n, (our_id, osm_name) in enumerate(sorted(pairs.items()), 1):
        target = CACHE / f"{our_id}.json"
        if target.exists() and not force:
            print(f"  [{n:2}/{len(pairs)}] {our_id:<18} cached")
            continue
        query = (
            "[out:json][timeout:300];"
            f'rel["admin_level"="5"]["name"="{osm_name}"]->.d;'
            ".d map_to_area->.a;"
            f'node["place"~"^({PLACE_KINDS})$"]["name"](area.a);'
            "out body;"
        )
        try:
            elements = overpass(query)["elements"]
        except Exception as error:  # noqa: BLE001 - report and continue; re-run resumes
            print(f"  [{n:2}/{len(pairs)}] {our_id:<18} FAILED {error}", file=sys.stderr)
            continue
        write_json(target, elements)
        print(f"  [{n:2}/{len(pairs)}] {our_id:<18} {len(elements):>5} places")
        time.sleep(PAUSE_S)


# --------------------------------------------------------------------------- build


def load_osm_places():
    places = []
    for path in sorted(CACHE.glob("*.json")):
        district = path.stem
        for element in read_json(path):
            tags = element.get("tags", {})
            name = tags.get("name")
            if not name:
                continue
            aliases = []
            for key in ("alt_name", "old_name", "name:en", "official_name"):
                value = tags.get(key)
                if value:
                    aliases.extend(part.strip() for part in value.split(";") if part.strip())
            places.append(
                {
                    "osm_id": f"node/{element['id']}",
                    "name": name,
                    "names": {
                        "en": tags.get("name:en", name),
                        "ta": tags.get("name:ta", ""),
                        "hi": tags.get("name:hi", ""),
                    },
                    "aliases": sorted({a for a in aliases if norm(a) != norm(name)}),
                    "kind": tags.get("place", ""),
                    "lat": element["lat"],
                    "lon": element["lon"],
                    "district": district,
                    "source": "OpenStreetMap",
                    "source_url": f"https://www.openstreetmap.org/node/{element['id']}",
                }
            )
    return places


def index_by_district(places):
    """Two indexes per district: strict normalised names, and folded keys."""
    index = {}
    for place in places:
        tables = index.setdefault(place["district"], {"strict": {}, "folded": {}})
        for name in {place["name"], *place["aliases"], *(v for v in place["names"].values() if v)}:
            tables["strict"].setdefault(norm(name), []).append(place)
            tables["folded"].setdefault(fold(name), []).append(place)
    return index


def match(name, district, index, fuzzy_floor=0.88):
    """Strict name, then romanisation-folded name, then a conservative fuzzy pass.

    Fuzzy runs on folded keys so the threshold measures real difference rather
    than spelling convention.
    """
    tables = index.get(district)
    if not tables:
        return None, 0.0, "none"
    strict, folded = tables["strict"], tables["folded"]
    key = norm(name)
    if key in strict:
        return strict[key][0], 1.0, "exact"
    folded_key = fold(name)
    if folded_key in folded:
        return folded[folded_key][0], 1.0, "exact"
    close = difflib.get_close_matches(folded_key, list(folded), 1, fuzzy_floor)
    if close:
        score = round(difflib.SequenceMatcher(None, folded_key, close[0]).ratio(), 3)
        return folded[close[0]][0], score, "fuzzy"
    return None, 0.0, "none"


def centroid(points):
    return (
        round(sum(p[0] for p in points) / len(points), 6),
        round(sum(p[1] for p in points) / len(points), 6),
    )


def build():
    places = load_osm_places()
    if not places:
        sys.exit("no cached OSM places -- run 'fetch' first")
    index = index_by_district(places)
    print(f"loaded {len(places)} OSM places across {len(index)} districts")

    district_centre = {}
    for place in places:
        district_centre.setdefault(place["district"], []).append((place["lat"], place["lon"]))
    district_centre = {d: centroid(pts) for d, pts in district_centre.items()}

    # Pass 1: direct name matches, which also give us block centres for pass 2.
    tables = {}
    block_points = {}
    stats = {"exact": 0, "fuzzy": 0, "none": 0}
    for filename in ("villages.json", "blocks.json"):
        rows = read_json(DATA / filename)
        for row in rows:
            place, score, how = match(row["name"], row["district"], index)
            stats[how] += 1
            row["geo_status"] = how
            if place is None:
                continue
            row.update(
                lat=place["lat"],
                lon=place["lon"],
                matched_name=place["name"],
                match_score=score,
                geo_precision="exact" if how == "exact" else "fuzzy",
                geo_source="OpenStreetMap",
                geo_source_url=place["source_url"],
            )
            key = (row["district"], row.get("block", row["name"]))
            block_points.setdefault(key, []).append((place["lat"], place["lon"]))
        tables[filename] = rows
    block_centre = {k: centroid(v) for k, v in block_points.items()}

    # Pass 2: every remaining row falls back to its block centre, then its
    # district centre. A row never carries a null coordinate -- it carries a
    # coarser one, labelled. OSM place coverage across Tamil Nadu is uneven, so
    # silently dropping unmatched villages would hide most of a district.
    fallbacks = {"block_centroid": 0, "district_centroid": 0, "unplaced": 0}
    for filename, rows in tables.items():
        for row in rows:
            if row.get("lat") is not None:
                continue
            key = (row["district"], row.get("block", row["name"]))
            if key in block_centre:
                lat, lon = block_centre[key]
                precision = "block_centroid"
            elif row["district"] in district_centre:
                lat, lon = district_centre[row["district"]]
                precision = "district_centroid"
            else:
                fallbacks["unplaced"] += 1
                row["lat"] = row["lon"] = None
                row["geo_precision"] = "unplaced"
                continue
            fallbacks[precision] += 1
            row.update(
                lat=lat, lon=lon, geo_precision=precision,
                geo_source="derived from OpenStreetMap place nodes",
            )
        write_json(DATA / filename, rows)
        placed = sum(1 for r in rows if r.get("lat") is not None)
        print(f"  wrote {filename} ({placed}/{len(rows)} placed)")

    # Localities OSM knows about that the rural directory never listed --
    # Saravanampatti is a Coimbatore suburb, not a TNRD village, which is why
    # it could never be found before.
    known = set()
    for rows in tables.values():
        for row in rows:
            known.add((row["district"], norm(row.get("matched_name") or row["name"])))
    extra = [
        {
            "id": f"osm:{p['osm_id'].split('/')[1]}",
            "name": p["name"],
            "names": p["names"],
            "aliases": p["aliases"],
            "kind": p["kind"],
            "district": p["district"],
            "lat": p["lat"],
            "lon": p["lon"],
            "geo_precision": "exact",
            "source": "OpenStreetMap",
            "source_url": p["source_url"],
        }
        for p in places
        if (p["district"], norm(p["name"])) not in known
    ]
    write_json(DATA / "localities.json", extra)
    print(f"  wrote localities.json ({len(extra)} places absent from the rural directory)")

    aliases = {}
    for place in places:
        variants = {*place["aliases"], *(v for v in place["names"].values() if v)}
        canonical = norm(place["name"])
        for variant in variants:
            key = norm(variant)
            if key and key != canonical:
                aliases[key] = sorted(set(aliases.get(key, [])) | {canonical})
    write_json(DATA / "aliases.json", aliases)
    print(f"  wrote aliases.json ({len(aliases)} spelling variants)")

    total = sum(stats.values())
    named = stats["exact"] + stats["fuzzy"]
    print(
        f"\ncoverage: {named}/{total} rows matched an OSM place by name "
        f"({named / total:.1%}) -- exact {stats['exact']}, fuzzy {stats['fuzzy']}"
    )
    print(
        f"          fallbacks: {fallbacks['block_centroid']} block centroid, "
        f"{fallbacks['district_centroid']} district centroid, "
        f"{fallbacks['unplaced']} unplaced"
    )


def report():
    for filename in ("villages.json", "blocks.json"):
        rows = read_json(DATA / filename)
        have = sum(1 for r in rows if r.get("lat") is not None)
        print(f"{filename:<16} {have}/{len(rows)} with coordinates ({have / len(rows):.1%})")
    for filename in ("localities.json", "aliases.json"):
        path = DATA / filename
        if path.exists():
            print(f"{filename:<16} {len(read_json(path))} entries")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["fetch", "build", "report"])
    parser.add_argument("--force", action="store_true", help="re-fetch cached districts")
    args = parser.parse_args()
    {"fetch": lambda: fetch(args.force), "build": build, "report": report}[args.stage]()
