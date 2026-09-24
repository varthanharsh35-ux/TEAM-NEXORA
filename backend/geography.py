"""User-triggered map lookups; persistent last-good cache, no invented POIs."""
import json,os,sqlite3,time,threading
from contextlib import closing
from pathlib import Path
import httpx
from fastapi import HTTPException
from intelligence import district_of,norm
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data/maps.sqlite3'
LOCK=threading.Lock();LAST=0
def cached(key,value=None):
 with closing(sqlite3.connect(DB)) as c:
  c.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY,body TEXT,updated REAL)')
  if value is not None:c.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',(key,json.dumps(value),time.time()));c.commit();return value
  row=c.execute('SELECT body,updated FROM cache WHERE key=?',(key,)).fetchone()
  return (json.loads(row[0]),row[1]) if row else None
def unpack(row):
 if row.get('address',{}).get('state')!='Tamil Nadu':return None
 d=district_of(row.get('display_name',''))
 return {'location':row['display_name'][:200],'lat':float(row['lat']),'lon':float(row['lon']),'district':d['id'] if d else '', 'source':'OpenStreetMap','source_url':f"https://www.openstreetmap.org/{row['osm_type']}/{row['osm_id']}"}
def search(q):
 global LAST
 key='search:'+norm(q);old=cached(key)
 if old and time.time()-old[1]<30*86400:return {'items':old[0],'cached':True}
 try:
  import main
  with main.GEOCODE_LOCK:
   if time.monotonic()-main.GEOCODE_LAST<1:raise HTTPException(429,detail='map_wait')
   main.GEOCODE_LAST=time.monotonic()
  with httpx.Client(timeout=12) as c:
   r=c.get(os.getenv('GEOCODER_URL','https://nominatim.openstreetmap.org')+'/search',params={'q':q if 'tamil' in q.lower() else q+', Tamil Nadu, India','format':'jsonv2','addressdetails':1,'countrycodes':'in','limit':5},headers={'User-Agent':'GramSahayak-SIH26091-prototype/2.0'})
   r.raise_for_status();items=[x for row in r.json() if (x:=unpack(row))]
  cached(key,items);return {'items':items,'cached':False}
 except HTTPException:raise
 except Exception:
  if old:return {'items':old[0],'cached':True,'stale':True}
  raise HTTPException(503,detail='map_failed')

# Each tuple is an OR set; adjacent bracket filters within a selector are ANDed.
# Broad legacy category IDs resolve through the declarative aliases below.
TAGS = {
    "poultry.broiler": {
        "direct": (
            '["shop"~"^butcher$"]',
            '["landuse"~"^farmyard$"]["poultry"]["poultry"!="no"]',
            '["landuse"~"^farmyard$"]["farmyard"~"^poultry$"]',
            '["man_made"~"^poultry$"]',
        ),
        "adjacent": (
            '["shop"~"^supermarket$|^convenience$"]',
            '["amenity"~"^marketplace$"]',
        ),
    },
    "dairy.milk": {
        "direct": ('["shop"~"^dairy$"]', '["man_made"~"^milk_chilling$"]'),
        "adjacent": ('["shop"~"^convenience$|^supermarket$"]',),
    },
    "retail.grocery": {
        "direct": ('["shop"~"^convenience$|^supermarket$|^general$"]',),
        "adjacent": ('["amenity"~"^marketplace$"]',),
    },
    "food.cafe": {
        "direct": ('["amenity"~"^cafe$"]',),
        "adjacent": ('["amenity"~"^restaurant$|^fast_food$"]',),
    },
    "food.restaurant": {
        "direct": ('["amenity"~"^restaurant$"]',),
        "adjacent": ('["amenity"~"^cafe$|^fast_food$"]',),
    },
    "food.fast_food": {
        "direct": ('["amenity"~"^fast_food$"]',),
        "adjacent": ('["amenity"~"^restaurant$|^cafe$"]',),
    },
    "tailoring.stitching": {
        "direct": ('["shop"~"^tailor$"]', '["craft"~"^tailor$"]'),
        "adjacent": ('["shop"~"^clothes$"]',),
    },
    "agriculture.inputs": {
        "direct": ('["shop"~"^agrarian$"]',),
        "adjacent": ('["shop"~"^farm$"]',),
    },
    "fish.retail": {
        "direct": ('["shop"~"^seafood$"]',),
        "adjacent": ('["shop"~"^supermarket$"]', '["amenity"~"^marketplace$"]'),
    },
    "repair.vehicle": {
        "direct": ('["shop"~"^car_repair$"]',),
        "adjacent": ('["shop"~"^car_parts$|^tyres$"]',),
    },
    "repair.bicycle": {
        "direct": ('["shop"~"^bicycle$"]',),
        "adjacent": (),
    },
    "repair.electronics": {
        "direct": ('["craft"~"^electronics_repair$"]',),
        "adjacent": ('["shop"~"^electronics$"]',),
    },
    "craft.handicrafts": {
        "direct": ('["shop"~"^craft$"]',),
        "adjacent": ('["shop"~"^gift$"]',),
    },
    "manufacturing": {
        "direct": ('["craft"]', '["man_made"~"^works$"]'),
        "adjacent": ('["landuse"~"^industrial$"]',),
    },
    "transport.taxi": {
        "direct": ('["amenity"~"^taxi$"]',),
        "adjacent": (),
    },
    "services.hairdresser": {
        "direct": ('["shop"~"^hairdresser$"]',),
        "adjacent": ('["shop"~"^beauty$"]',),
    },
    "services.beauty": {
        "direct": ('["shop"~"^beauty$"]',),
        "adjacent": ('["shop"~"^hairdresser$"]',),
    },
    "services.laundry": {
        "direct": ('["shop"~"^laundry$"]',),
        "adjacent": ('["shop"~"^dry_cleaning$"]',),
    },
    "food": {
        "direct": ('["amenity"~"^restaurant$|^cafe$|^fast_food$"]',),
        "adjacent": (),
    },
    "repair": {
        "direct": ('["shop"~"^car_repair$|^bicycle$"]', '["craft"~"^electronics_repair$"]'),
        "adjacent": ('["shop"~"^electronics$"]',),
    },
    "services": {
        "direct": ('["shop"~"^hairdresser$|^beauty$|^laundry$"]',),
        "adjacent": (),
    },
    "other": {"direct": (), "adjacent": ()},
}
for alias, activity in {
    "poultry": "poultry.broiler",
    "poultry.layer": "poultry.broiler",
    "dairy": "dairy.milk",
    "retail": "retail.grocery",
    "tailoring": "tailoring.stitching",
    "agriculture": "agriculture.inputs",
    "fish": "fish.retail",
    "craft": "craft.handicrafts",
    "transport": "transport.taxi",
}.items():
    TAGS[alias] = TAGS[activity]


def nearby(lat, lon, category, radius_km=15, cache_only=False):
    """Return contract map layers, rechecking both tags and radial distance.

    This task supplies competition and amenity observations. Drivers remain empty
    until the evidence-backed driver engine is available; no effects are inferred
    from arbitrary returned POIs. Way/relation distances use their returned centre.
    """
    import math
    import re
    from datetime import datetime, timedelta, timezone

    global LAST

    def fail(code, status_code, reason):
        raise HTTPException(
            status_code,
            detail={
                "error": code,
                "message_key": f"errors.{code}",
                "status": "unresolved",
                "detail": {"reason": reason},
                "candidates": [],
            },
        )

    try:
        lat = float(lat)
        lon = float(lon)
        radius_km = float(radius_km)
    except (TypeError, ValueError):
        fail("invalid_input", 422, "invalid_coordinates_or_radius")
    if not all(math.isfinite(value) for value in (lat, lon, radius_km)):
        fail("invalid_input", 422, "non_finite_coordinates_or_radius")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or radius_km not in (5, 10, 15):
        fail("invalid_input", 422, "invalid_coordinates_or_radius")
    if category not in TAGS:
        fail("invalid_input", 422, "unknown_activity")

    selectors = TAGS[category]
    # An activity with no selector cannot be searched for. An empty competitor
    # layer must then read as "we did not look", never as "there is none"
    # (RULES.md rule 6), so the response is labelled differently.
    has_selectors = bool(selectors["direct"] or selectors["adjacent"])
    radius_m = int(radius_km * 1000)
    source_url = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    # Versioned namespace prevents the old mixed-layer cache from leaking into v3.
    key = f"nearby:v3-layers:{lat}:{lon}:{category}:{radius_m}:{source_url}"
    try:
        old = cached(key)
    except sqlite3.Error:
        old = None
    if old and not isinstance(old[0].get("layers"), dict):
        old = None
    if old and time.time() - old[1] < 7 * 86400:
        return old[0]
    # Report generation reads observations, it does not go and fetch them. A
    # synchronous user-facing request must never block on Overpass, and tests
    # must never reach the network.
    if cache_only:
        return None

    # This parser handles only the declarative tag selectors above, never user QL.
    pattern = re.compile(r'\["([^"\]]+)"(?:(~|!=|=)"([^"\]]*)")?\]')

    def matches(tags, selector):
        conditions = list(pattern.finditer(selector))
        if not conditions or "".join(part.group() for part in conditions) != selector:
            raise ValueError("unsupported_selector")
        for part in conditions:
            name, operator, expected = part.groups()
            actual = tags.get(name)
            if operator is None and actual is None:
                return False
            if operator == "=" and actual != expected:
                return False
            if operator == "!=" and actual == expected:
                return False
            if operator == "~" and (not isinstance(actual, str) or re.fullmatch(expected, actual) is None):
                return False
        return True

    def distance_m(point_lat, point_lon):
        delta_lat = math.radians(point_lat - lat)
        delta_lon = math.radians(point_lon - lon)
        haversine = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(math.radians(lat))
            * math.cos(math.radians(point_lat))
            * math.sin(delta_lon / 2) ** 2
        )
        return 6371008.8 * 2 * math.asin(math.sqrt(min(1, max(0, haversine))))

    try:
        with LOCK:
            if time.monotonic() - LAST < 2:
                fail("rate_limited", 429, "overpass_request_interval")
            LAST = time.monotonic()
        around = f"(around:{radius_m},{lat},{lon})"
        import drivers as driver_engine
        selected = dict.fromkeys(
            ('["amenity"~"^bank$|^post_office$"]',)
            + tuple(selectors["direct"])
            + tuple(selectors["adjacent"])
            + tuple(driver_engine.all_selectors())
        )
        clauses = "".join(f"nwr{selector}{around};" for selector in selected)
        query = f"[out:json][timeout:12];({clauses});out center 800;"
        with httpx.Client(timeout=16) as client:
            response = client.get(
                source_url,
                params={"data": query},
                headers={"User-Agent": "GramSahayak-SIH26091-prototype/3.0"},
            )
            response.raise_for_status()
            raw = response.json()
        if not isinstance(raw, dict) or not isinstance(raw.get("elements"), list) or raw.get("remark"):
            fail("source_unavailable", 503, "invalid_or_incomplete_overpass_response")

        retrieved_at = datetime.now(timezone.utc)
        observed = retrieved_at.date().isoformat()
        provenance = {
            "method": "measured",
            "source": "OpenStreetMap via Overpass",
            "source_url": source_url,
            "retrieved_at": retrieved_at.isoformat(),
        }
        layers = {"competitors": [], "drivers": [], "amenities": []}
        seen = set()
        for item in raw["elements"]:
            if not isinstance(item, dict):
                continue
            tags = item.get("tags", {})
            coords = item.get("center", item)
            if not isinstance(tags, dict) or not isinstance(coords, dict):
                continue
            # Disallowed amenities cannot fall through, even in an overbroad/stale response.
            if tags.get("amenity") == "blood_bank":
                continue
            try:
                point_lat = float(coords["lat"])
                point_lon = float(coords["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            if not (math.isfinite(point_lat) and math.isfinite(point_lon)):
                continue
            if not (-90 <= point_lat <= 90 and -180 <= point_lon <= 180):
                continue
            distance = distance_m(point_lat, point_lon)
            if distance > radius_m:
                continue
            if item.get("type") not in ("node", "way", "relation") or not isinstance(item.get("id"), int):
                continue
            identity = f"{item['type']}/{item['id']}"
            if identity in seen:
                continue
            seen.add(identity)
            point = {
                "id": identity,
                "lat": point_lat,
                "lon": point_lon,
                "name": tags.get("name", ""),
            }
            amenity = tags.get("amenity")
            if amenity in ("bank", "post_office"):
                layers["amenities"].append({
                    **point,
                    "kind": amenity,
                    "emoji": {"bank": "\U0001f3e6", "post_office": "\U0001f3e4"}[amenity],
                })
                continue
            match = next(
                (kind for kind in ("direct", "adjacent") if any(
                    matches(tags, selector) for selector in selectors[kind]
                )),
                None,
            )
            if match is not None:
                layers["competitors"].append({
                    **point,
                    "distance_m": round(distance),
                    "match": match,
                    "emoji": "\U0001f3ea",
                })
        layers["competitors"].sort(key=lambda point: (point["distance_m"], point["id"]))
        layers["drivers"].sort(key=lambda point: (point["distance_m"], point["id"]))
        assessment = driver_engine.score(category, layers["drivers"], layers["competitors"])
        result = {
            "layers": layers,
            "centre": {"lat": lat, "lon": lon},
            "radius_km": int(radius_km),
            "drivers": assessment["drivers"],
            "demand_score": assessment["demand_score"],
            "observed": observed,
            "completeness": "partial" if has_selectors else "unknown",
            "completeness_note_key": (
                "notes.osm_partial" if has_selectors else "notes.no_competitor_selector"
            ),
            "provenance": provenance,
            "freshness": {
                "dataset": "osm_nearby",
                "version": retrieved_at.isoformat(),
                "last_verified": observed,
                "next_check": (retrieved_at + timedelta(days=7)).date().isoformat(),
                "status": "fresh",
            },
        }
    except (httpx.HTTPError, ValueError, TypeError, HTTPException) as exc:
        if old:
            result = dict(old[0])
            result["freshness"] = {**result["freshness"], "status": "stale"}
            return result
        if isinstance(exc, HTTPException):
            raise
        fail("source_unavailable", 503, "overpass_unavailable")
    try:
        cached(key, result)
    except sqlite3.Error:
        # Successful observations remain usable if the optional cache cannot be written.
        pass
    return result
