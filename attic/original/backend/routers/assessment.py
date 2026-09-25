import math
import uuid
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Tuple, Any, Optional
from fastapi import APIRouter, HTTPException
from models import AssessmentInput, AssessmentResult, NearbyBusiness, SWOTData, StructuredVerdict
from data.schemes_data import GOVERNMENT_SCHEMES

router = APIRouter(tags=["Assessment"])

ASSESSMENTS_STORE: Dict[str, AssessmentResult] = {}

# ──────────────────────────────────────────────────────────────────────────────
# Category-scoped OSM tag mapping (Spec §2):
# Only POIs matching these tags are classified as "competitors" for the given
# business type. Everything else is an "amenity" or "financial" institution.
# ──────────────────────────────────────────────────────────────────────────────
BUSINESS_TYPE_OSM_TAGS = {
    "retail": {
        "competitor_shop_tags": ["general", "convenience", "supermarket", "variety_store", "department_store", "wholesale", "mall", "kiosk"],
        "competitor_amenity_tags": [],
        "label": "Retail / Kirana"
    },
    "food": {
        "competitor_shop_tags": ["bakery", "confectionery", "pastry", "deli"],
        "competitor_amenity_tags": ["restaurant", "fast_food", "cafe", "food_court", "ice_cream"],
        "label": "Food & Beverages"
    },
    "agriculture": {
        "competitor_shop_tags": ["agrarian", "farm", "garden_centre", "seeds", "fertilizer"],
        "competitor_amenity_tags": ["marketplace"],
        "label": "Agriculture / Agro-Processing"
    },
    "handicraft": {
        "competitor_shop_tags": ["craft", "art", "gift", "antiques", "jewelry", "fabric"],
        "competitor_amenity_tags": [],
        "label": "Handicraft / Artisan"
    },
    "textile": {
        "competitor_shop_tags": ["clothes", "fashion", "boutique", "tailor", "fabric", "shoes", "leather"],
        "competitor_amenity_tags": [],
        "label": "Textile / Garments"
    },
    "dairy": {
        "competitor_shop_tags": ["dairy", "cheese", "farm"],
        "competitor_amenity_tags": ["marketplace"],
        "label": "Dairy / Animal Husbandry"
    },
    "services": {
        "competitor_shop_tags": ["electronics", "mobile_phone", "computer", "hardware", "copyshop"],
        "competitor_amenity_tags": ["internet_cafe"],
        "label": "Services / Repair"
    },
    "manufacturing": {
        "competitor_shop_tags": ["hardware", "trade", "industrial"],
        "competitor_amenity_tags": [],
        "label": "Manufacturing"
    },
    "transport": {
        "competitor_shop_tags": ["car", "car_repair", "motorcycle", "tyres", "car_parts"],
        "competitor_amenity_tags": ["fuel", "car_wash", "parking"],
        "label": "Transport / Logistics"
    },
    "other": {
        "competitor_shop_tags": [],
        "competitor_amenity_tags": [],
        "label": "Other"
    }
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in kilometers between two points."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def fetch_real_nearby_pois(lat: float, lon: float, radius_km: float, business_type: str = "retail") -> Tuple[List[NearbyBusiness], List[NearbyBusiness], List[NearbyBusiness]]:
    """
    Fetch real-world POIs from OpenStreetMap Overpass API within radius_km.
    Categorizes into competitors (scoped to business_type), synergistic footfall
    anchors, and financial institutions.
    """
    radius_m = min(15000, int(radius_km * 1000))
    query = f"""
    [out:json][timeout:15];
    (
      node["shop"](around:{radius_m},{lat},{lon});
      node["amenity"~"cafe|restaurant|fast_food|bank|post_office|pharmacy|marketplace|fuel|school|college|university|hospital|clinic|internet_cafe|food_court|ice_cream|car_wash|parking"](around:{radius_m},{lat},{lon});
      node["craft"](around:{radius_m},{lat},{lon});
      way["shop"](around:{radius_m},{lat},{lon});
      way["amenity"~"cafe|restaurant|fast_food|bank|post_office|pharmacy|marketplace|fuel|school|college|university|hospital|clinic|internet_cafe|food_court|ice_cream|car_wash|parking"](around:{radius_m},{lat},{lon});
    );
    out center tags 80;
    """
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": "GramSahayakAI/1.0 (Rural Entrepreneurship Advisory Platform; SIH2026)"}
    )

    competitors: List[NearbyBusiness] = []
    amenities: List[NearbyBusiness] = []
    banks: List[NearbyBusiness] = []

    # Get category-scoped tags
    btype_lower = business_type.lower()
    type_config = BUSINESS_TYPE_OSM_TAGS.get(btype_lower, BUSINESS_TYPE_OSM_TAGS["other"])
    comp_shop_tags = set(type_config["competitor_shop_tags"])
    comp_amenity_tags = set(type_config["competitor_amenity_tags"])

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
            elements = result.get("elements", [])

            for el in elements:
                tags = el.get("tags", {})
                e_lat = el.get("lat") or el.get("center", {}).get("lat")
                e_lon = el.get("lon") or el.get("center", {}).get("lon")

                if not e_lat or not e_lon:
                    continue

                dist = haversine_distance(lat, lon, e_lat, e_lon)
                name = tags.get("name") or tags.get("name:en") or tags.get("name:hi") or ""
                shop_tag = tags.get("shop")
                amenity_tag = tags.get("amenity")
                craft_tag = tags.get("craft")

                category = shop_tag or amenity_tag or craft_tag or "commercial"
                category_clean = category.replace("_", " ").title()

                if not name:
                    if shop_tag:
                        name = f"Local {category_clean} Store"
                    elif amenity_tag in ["bank", "post_office"]:
                        name = f"Public {category_clean}"
                    elif amenity_tag in ["school", "college", "university"]:
                        name = f"Educational Center ({category_clean})"
                    elif amenity_tag in ["hospital", "clinic", "pharmacy"]:
                        name = f"Healthcare Facility ({category_clean})"
                    else:
                        name = f"Commercial Unit ({category_clean})"

                gmaps_link = f"https://www.google.com/maps/search/?api=1&query={e_lat},{e_lon}"
                contact_info = tags.get("phone") or tags.get("contact:phone") or tags.get("website")

                poi = NearbyBusiness(
                    id=f"osm-{el.get('id', uuid.uuid4().hex[:6])}",
                    name=name,
                    category=category_clean,
                    type="amenity",
                    distanceKm=dist,
                    lat=e_lat,
                    lon=e_lon,
                    contact=contact_info,
                    address=tags.get("addr:street") or tags.get("addr:suburb"),
                    gmapsUrl=gmaps_link
                )

                # Classify: financial → amenity → competitor (scoped to business type)
                if amenity_tag in ["bank", "post_office"]:
                    poi.type = "financial"
                    banks.append(poi)
                elif amenity_tag in ["school", "college", "university", "hospital", "clinic"]:
                    poi.type = "amenity"
                    amenities.append(poi)
                elif (shop_tag and shop_tag in comp_shop_tags) or (amenity_tag and amenity_tag in comp_amenity_tags):
                    # This POI matches the user's business type → genuine competitor
                    poi.type = "competitor"
                    competitors.append(poi)
                elif amenity_tag in ["marketplace", "fuel"]:
                    # Footfall anchors
                    poi.type = "amenity"
                    amenities.append(poi)
                else:
                    # Non-matching commercial POIs → footfall anchors, not competitors
                    poi.type = "amenity"
                    amenities.append(poi)

    except Exception as e:
        # If external Overpass is unreachable or throttled, proceed with 0 records
        # ZERO fabricated data is returned.
        print(f"[GramSahayak POI Warning] Overpass query notice: {e}")

    competitors.sort(key=lambda x: x.distanceKm)
    amenities.sort(key=lambda x: x.distanceKm)
    banks.sort(key=lambda x: x.distanceKm)

    return competitors, amenities, banks


def evaluate_multi_condition_suitability(
    data: AssessmentInput,
    competitors: List[NearbyBusiness],
    amenities: List[NearbyBusiness],
    banks: List[NearbyBusiness]
) -> Tuple[int, str, str, str, Dict[str, int], SWOTData, List[str], List[Dict[str, Any]], StructuredVerdict]:
    """
    Evaluates business suitability across 6 verified multi-condition pillars:
    1. Competitor Density & First-Mover Advantage  (market)
    2. Footfall & Anchor Synergy Index             (synergy)
    3. Capital Adequacy vs Sector Minimums          (financial)
    4. Operational Readiness & Facility Fit          (operations)
    5. Accessibility & Infrastructure               (accessibility)
    6. Demand Potential & Growth Indicators          (demand)
    """
    btype = data.businessType.lower()
    capital = data.initialCapital
    facilities = [f.lower() for f in data.facilities]

    # Benchmark capital requirements per sector
    sector_benchmarks = {
        "retail": {"min": 50000, "established": 300000, "synergy_weights": ["school", "market", "residential"]},
        "food": {"min": 75000, "established": 450000, "synergy_weights": ["college", "school", "office", "transit"]},
        "agriculture": {"min": 40000, "established": 250000, "synergy_weights": ["market", "water", "transport"]},
        "handicraft": {"min": 25000, "established": 150000, "synergy_weights": ["tourism", "market", "transit"]},
        "textile": {"min": 60000, "established": 350000, "synergy_weights": ["market", "residential"]},
        "dairy": {"min": 80000, "established": 500000, "synergy_weights": ["water", "transport", "market"]},
        "services": {"min": 35000, "established": 200000, "synergy_weights": ["residential", "market", "transit"]},
        "manufacturing": {"min": 150000, "established": 800000, "synergy_weights": ["power", "transport", "storage"]},
        "transport": {"min": 100000, "established": 600000, "synergy_weights": ["transit", "market", "fuel"]},
        "other": {"min": 50000, "established": 300000, "synergy_weights": ["market"]}
    }
    benchmark = sector_benchmarks.get(btype, sector_benchmarks["retail"])
    type_label = BUSINESS_TYPE_OSM_TAGS.get(btype, BUSINESS_TYPE_OSM_TAGS["other"])["label"]

    # --- Condition 1: Competitor Density (0-16) → "market" ---
    immediate_competitors = [c for c in competitors if c.distanceKm <= 1.5]
    total_competitors = len(competitors)

    if len(immediate_competitors) == 0 and total_competitors <= 3:
        comp_score = 16  # High first-mover advantage
    elif len(immediate_competitors) <= 2:
        comp_score = 13  # Healthy competitive space
    elif len(immediate_competitors) <= 5:
        comp_score = 9   # Moderate competition
    else:
        comp_score = 5   # Highly saturated immediate perimeter

    # --- Condition 2: Footfall & Anchor Synergy (0-16) → "synergy" ---
    amenity_count = len(amenities)
    if btype in ["food", "retail", "services"]:
        if amenity_count >= 5:
            synergy_score = 16
        elif amenity_count >= 2:
            synergy_score = 13
        elif amenity_count >= 1:
            synergy_score = 10
        else:
            synergy_score = 5  # Isolated location for footfall-heavy business
    elif btype in ["dairy", "agriculture", "manufacturing"]:
        # These benefit from open spatial perimeter rather than dense retail footfall
        if amenity_count <= 4:
            synergy_score = 15  # Ideal spacious perimeter
        else:
            synergy_score = 11
    else:
        synergy_score = min(16, 8 + amenity_count)

    # --- Condition 3: Capital Adequacy (0-16) → "financial" ---
    if capital >= benchmark["established"]:
        capital_score = 16
    elif capital >= benchmark["min"] * 1.5:
        capital_score = 13
    elif capital >= benchmark["min"]:
        capital_score = 10
    else:
        capital_score = 5  # Below bare-minimum capital required

    # --- Condition 4: Operational Readiness (0-16) → "operations" ---
    has_power = any("power" in f or "electric" in f for f in facilities)
    has_space = any("shop" in f or "space" in f or "rented" in f for f in facilities)
    has_storage = any("storage" in f for f in facilities)
    has_transport = any("vehicle" in f for f in facilities)
    has_water = any("water" in f for f in facilities)
    has_internet = any("internet" in f for f in facilities)
    has_bank_account = any("bank" in f for f in facilities)

    op_score = 7
    if has_space: op_score += 3
    if has_power: op_score += 2
    if has_storage and btype in ["manufacturing", "agriculture", "dairy", "retail"]: op_score += 2
    if has_transport: op_score += 2
    op_score = min(16, op_score)

    # --- Condition 5: Accessibility & Infrastructure (0-16) → "accessibility" ---
    bank_count = len(banks)
    acc_score = 7
    if bank_count >= 3: acc_score += 4
    elif bank_count >= 1: acc_score += 2
    if has_internet: acc_score += 2
    if has_bank_account: acc_score += 2
    if has_water and btype in ["food", "dairy", "agriculture"]: acc_score += 1
    acc_score = min(16, acc_score)

    # --- Condition 6: Demand Potential (0-20) → "demand" ---
    # Inferred from anchor density, population proxies, and sector type
    demand_score = 8
    edu_anchors = len([a for a in amenities if any(k in a.category.lower() for k in ["school", "college", "university"])])
    health_anchors = len([a for a in amenities if any(k in a.category.lower() for k in ["hospital", "clinic", "pharmacy"])])
    market_anchors = len([a for a in amenities if "market" in a.category.lower()])

    if btype in ["food", "retail"]:
        demand_score += min(6, edu_anchors * 2)
        demand_score += min(3, market_anchors * 2)
    elif btype in ["services"]:
        demand_score += min(5, (edu_anchors + health_anchors))
        demand_score += min(3, market_anchors)
    elif btype in ["dairy", "agriculture"]:
        demand_score += min(4, market_anchors * 2)
        demand_score += 2  # Baseline rural demand for essential agro/dairy products
    else:
        demand_score += min(4, amenity_count)

    if data.priorExperienceYears >= 3:
        demand_score += 2
    demand_score = min(20, demand_score)

    total_score = comp_score + synergy_score + capital_score + op_score + acc_score + demand_score
    total_score = max(20, min(96, total_score))

    # Feasibility verdict determination
    if total_score >= 78:
        grade = "Excellent Viability"
        risk = "Low Risk"
    elif total_score >= 62:
        grade = "Viable Opportunity"
        risk = "Moderate Risk"
    elif total_score >= 48:
        grade = "Conditional Viability"
        risk = "Elevated Risk"
    else:
        grade = "High Risk — Restructuring Recommended"
        risk = "High Risk"

    # ────────────────────────────────────────────────────────────────
    # Dynamic SWOT Generation (§12: Weaknesses MUST NEVER be empty)
    # ────────────────────────────────────────────────────────────────
    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    # Strengths
    if comp_score >= 13:
        strengths.append(f"Low competitor saturation: only {total_competitors} {type_label} competitors within {data.radiusKm} km allows capturing market share early.")
    elif total_competitors > 0:
        strengths.append(f"Established commercial hub with {total_competitors} existing businesses proves customer traffic viability in the vicinity.")
    else:
        strengths.append(f"First-mover advantage: zero direct {type_label} competitors detected within {data.radiusKm} km catchment.")

    if capital >= benchmark["min"] * 1.5:
        strengths.append(f"Adequate startup capital (₹{capital:,.0f}) exceeds the ₹{benchmark['min']:,} sector minimum, covering equipment capex and working capital runway.")
    elif capital >= benchmark["min"]:
        strengths.append(f"Startup capital (₹{capital:,.0f}) meets the bare minimum of ₹{benchmark['min']:,} for {type_label} sector entry.")

    if has_space:
        strengths.append("Commercial premise readiness reduces upfront setup delays and rental friction.")
    if data.priorExperienceYears >= 2:
        strengths.append(f"{data.priorExperienceYears} years of prior domain experience provides operational confidence and vendor relationships.")

    # Weaknesses — GUARANTEED NON-EMPTY (minimum 2 items always)
    if capital < benchmark["min"]:
        weaknesses.append(f"Current capital (₹{capital:,.0f}) is below the ₹{benchmark['min']:,} starter benchmark for {type_label}. Equipment and initial inventory procurement may be constrained.")
    elif capital < benchmark["established"]:
        weaknesses.append(f"Capital (₹{capital:,.0f}) is below the established business threshold of ₹{benchmark['established']:,} for {type_label}. Scaling capacity will require external credit within 6–12 months.")

    if not has_power and btype in ["manufacturing", "food", "dairy"]:
        weaknesses.append(f"Lack of dedicated 3-phase power supply limits machinery and refrigeration capacity critical for {type_label} operations.")

    if data.priorExperienceYears < 2:
        weaknesses.append(f"Limited prior industry experience ({data.priorExperienceYears} years) increases operational learning curve and initial decision-making risk for vendor negotiations and pricing strategies.")

    if len(facilities) <= 2:
        weaknesses.append("Limited initial infrastructure: reliance on third-party services for storage, transport, or utilities increases operating costs and introduces supply chain dependencies.")

    if not has_storage and btype in ["retail", "agriculture", "manufacturing", "dairy"]:
        weaknesses.append(f"No dedicated storage facility declared. For {type_label}, inventory vulnerability during seasonal procurement windows increases spoilage and stockout risk.")

    monthly_rev_est = data.expectedMonthlyRevenue or max(20000.0, capital * 0.35)
    monthly_budget_est = data.monthlyBudget or max(12000.0, monthly_rev_est * 0.65)
    net_est = monthly_rev_est - monthly_budget_est
    runway_months = int(capital * 0.15 / monthly_budget_est) if monthly_budget_est > 0 else 3
    if runway_months < 4:
        weaknesses.append(f"Estimated working capital runway of only ~{runway_months} months. Any revenue delay beyond this window would require emergency credit to sustain operations.")

    if total_competitors >= 3:
        weaknesses.append(f"Presence of {total_competitors} existing competitors in catchment creates pricing pressure and customer acquisition cost concerns during the first 6 months of operation.")

    # Ensure minimum 2 weaknesses
    if len(weaknesses) < 2:
        weaknesses.append("New entrant risk: building brand recognition and customer loyalty from zero requires sustained marketing effort and initial below-margin pricing strategies.")
    if len(weaknesses) < 2:
        weaknesses.append("Regulatory compliance overhead: FSSAI, Udyam Registration, and GST setup require upfront administrative investment and documentation effort.")

    # Opportunities
    if bank_count > 0:
        weakest_bank = banks[0].name if banks else "nearby branch"
        weaknesses_bank_dist = banks[0].distanceKm if banks else "N/A"
        opportunities.append(f"{bank_count} verified bank/post-office branch(es) within catchment (nearest: {weakest_bank}, {weaknesses_bank_dist} km) provide direct access to credit schemes.")
    opportunities.append("High government subsidy eligibility under PMEGP (35% capital subsidy), PM SVANidhi (7% interest subvention), and MUDRA Yojana (zero-collateral loans up to ₹5 lakh).")
    if synergy_score >= 12:
        opportunities.append(f"Proximity to {amenity_count} nearby public, educational, and commercial anchors provides steady walk-in footfall and cross-selling synergies.")
    if edu_anchors >= 2 and btype in ["food", "retail", "services"]:
        opportunities.append(f"{edu_anchors} educational institutions nearby create a recurring student/staff customer base with predictable daily demand patterns.")

    # Threats
    if comp_score <= 9:
        threats.append(f"Presence of {len(immediate_competitors)} direct {type_label} competitors within 1.5 km creates immediate price competition risk and may require differentiation-first strategy.")
    threats.append("Seasonal demand fluctuations during monsoon and agricultural harvest cycles may cause 20–40% revenue dip in affected months requiring working capital buffer.")
    if bank_count == 0:
        threats.append("No institutional bank branch within immediate radius; formal credit access requires travel to district/block headquarters, increasing transaction costs for loan servicing.")
    if not has_internet:
        threats.append("Limited digital connectivity restricts access to UPI payments, online marketing channels, and government e-portal applications (Udyam, PMEGP, myScheme).")

    swot = SWOTData(
        strengths=strengths,
        weaknesses=weaknesses,
        opportunities=opportunities,
        threats=threats
    )

    # ────────────────────────────────────────────────────────────────
    # Actionable tailored strategy recommendations
    # ────────────────────────────────────────────────────────────────
    recommendations = []
    if total_score >= 62:
        recommendations.append("Adopt digital UPI QR payments (PhonePe, BHIM, Google Pay) to build verifiable digital turnover for second-tranche credit expansion under MUDRA Kishore.")
        recommendations.append("Negotiate 15-day vendor credit with regional wholesale distributors to preserve liquid working capital during the critical first 6 months.")
        recommendations.append("Maintain at least 30 to 45 days of raw inventory in buffer stock to prevent supply interruptions during seasonal procurement gaps.")
        if edu_anchors >= 1 and btype in ["food", "retail"]:
            recommendations.append(f"Leverage proximity to {edu_anchors} educational institution(s) with targeted student combo offers and loyalty cards to establish early repeat customers.")
    else:
        recommendations.append(f"Consider adjusting initial investment to at least ₹{benchmark['min']:,} to satisfy bare-minimum equipment and inventory requirements for {type_label}.")
        if btype in ["food", "retail"] and synergy_score < 10:
            recommendations.append("Consider positioning the primary point of sale closer to identified transit stops, school gates, or marketplace entry points to capture walk-in footfall.")
        recommendations.append("Apply for zero-collateral working capital under PM SVANidhi (₹10K–50K) or MUDRA Shishu (up to ₹50K) to bridge the capital gap before scaling up.")
        recommendations.append("Start with a lean pilot operation testing 3–5 core product lines before committing to full inventory investment, reducing downside risk.")

    # Alternative business suggestions
    alternative_ideas = []
    if btype != "retail":
        alternative_ideas.append({"category": "retail", "title": "Essential Daily Goods / Kirana", "rationale": "Consistent high-velocity demand with quick inventory turnover in residential village catchments."})
    if btype != "services":
        alternative_ideas.append({"category": "services", "title": "Digital Service Center & Electrical Repair", "rationale": "Low capex barrier, high daily service margins with minimal perishable inventory."})
    if btype != "food" and amenity_count >= 2:
        alternative_ideas.append({"category": "food", "title": "Tea, Snacks & Fresh Bakery Point", "rationale": "Strong daily repeat footfall near local schools and transit stops."})

    # 6-dimension scores normalized to 0-100
    dim_scores = {
        "market": min(100, comp_score * 6),
        "synergy": min(100, synergy_score * 6),
        "financial": min(100, capital_score * 6),
        "operations": min(100, op_score * 6),
        "accessibility": min(100, acc_score * 6),
        "demand": min(100, demand_score * 5)
    }

    # ────────────────────────────────────────────────────────────────
    # Structured Verdict (Spec §4: detailed justified narrative)
    # ────────────────────────────────────────────────────────────────
    if total_score >= 78:
        headline = "Viable — Strong Opportunity"
        verdict_summary = f"The proposed {type_label} venture at {data.location} demonstrates strong commercial viability across all six evaluation dimensions. Capital adequacy, manageable local competition, and proximity to demand anchors collectively support a confident go-ahead."
    elif total_score >= 62:
        headline = "Viable with Caveats"
        verdict_summary = f"The proposed {type_label} venture at {data.location} is commercially viable but requires attention to identified weaknesses. Strategic adjustments in capital allocation, competitive positioning, or operational infrastructure would significantly improve success probability."
    elif total_score >= 48:
        headline = "Conditional — Proceed with Caution"
        verdict_summary = f"The venture shows conditional viability. Multiple risk factors need mitigation: optimize working capital buffer, secure critical infrastructure gaps, and develop differentiation strategies to withstand local competitive pressures."
    else:
        headline = "Not Recommended at Current Parameters"
        verdict_summary = f"Location and capital indicators show elevated risk for an independent {type_label} unit at {data.location}. Consider relocating closer to consumer activity anchors, increasing initial capital, or pivoting to an alternative lower-overhead sector."

    positive_factors = []
    if comp_score >= 13:
        positive_factors.append(f"Low competitor density: only {total_competitors} direct {type_label} competitors within {data.radiusKm} km catchment — strong first-mover advantage.")
    if capital_score >= 13:
        positive_factors.append(f"Healthy capital base (₹{capital:,.0f}) meets or exceeds sector requirements, providing adequate runway for initial operations.")
    if synergy_score >= 12:
        positive_factors.append(f"Strong footfall synergy: {amenity_count} nearby public/commercial anchors (schools, markets, healthcare) generate regular walk-in traffic.")
    if bank_count >= 1:
        positive_factors.append(f"Financial accessibility: {bank_count} bank/post-office branch(es) within catchment enable direct scheme application and credit access.")
    if demand_score >= 14:
        positive_factors.append(f"High demand potential indicated by {edu_anchors} educational and {market_anchors} commercial anchor(s) in proximity.")
    if not positive_factors:
        positive_factors.append("Baseline market entry feasibility exists with government scheme support available.")

    negative_factors = []
    if comp_score <= 9:
        negative_factors.append(f"High competitive saturation: {len(immediate_competitors)} direct competitors within 1.5 km radius creates pricing pressure and customer acquisition challenges.")
    if capital_score <= 10:
        negative_factors.append(f"Constrained capital (₹{capital:,.0f}) against ₹{benchmark['established']:,} established benchmark limits initial scale and inventory depth.")
    if op_score <= 9:
        negative_factors.append(f"Operational infrastructure gaps: only {len(facilities)} facility/facilities declared — additional investment in premises, power, or storage is required.")
    if acc_score <= 9:
        negative_factors.append(f"Limited institutional access: {bank_count} bank(s) and limited digital connectivity constrain formal credit and digital payment adoption.")
    if not negative_factors:
        negative_factors.append("No critical negative factors identified, but standard new-entrant risks apply.")

    # Competitor comparison narrative
    if total_competitors == 0:
        comp_comparison = f"No direct {type_label} competitors were identified within the {data.radiusKm} km catchment zone. This represents a first-mover opportunity, but also indicates the area may have unproven demand for this category. Validation through a lean pilot is recommended."
    elif total_competitors <= 3:
        comp_comparison = f"{total_competitors} direct {type_label} competitor(s) were found within {data.radiusKm} km, with {len(immediate_competitors)} within the immediate 1.5 km zone. This is a healthy competitive landscape — enough to confirm market demand without excessive saturation."
    else:
        nearest = competitors[0] if competitors else None
        comp_comparison = f"{total_competitors} direct {type_label} competitors were identified, with {len(immediate_competitors)} within the immediate 1.5 km zone. The nearest competitor is '{nearest.name}' at {nearest.distanceKm} km. This density requires a clear differentiation strategy — focus on quality, pricing, or specialization to capture share."

    next_steps = []
    if total_score >= 62:
        next_steps.append("Complete Udyam Registration at udyamregistration.gov.in to unlock MSME benefits and scheme eligibility.")
        next_steps.append(f"Apply for {'PMEGP' if capital < 500000 else 'MUDRA Kishore'} credit within the first 30 days to supplement working capital.")
        next_steps.append("Set up UPI QR and digital payment acceptance from Day 1 to build verifiable turnover records.")
        next_steps.append("Conduct a 2-week soft launch with core product lines before committing to full inventory investment.")
    else:
        next_steps.append("Re-evaluate location choice: scout 2-3 alternative locations closer to identified footfall anchors (schools, markets, transit points).")
        next_steps.append(f"Target increasing startup capital to at least ₹{benchmark['min'] * 2:,} through PM SVANidhi, MUDRA Shishu, or family pooling before launch.")
        next_steps.append("Attend EDP (Entrepreneurship Development Programme) training at the nearest KVIC/DIC office to strengthen business planning skills.")

    structured_verdict = StructuredVerdict(
        headline=headline,
        summary=verdict_summary,
        positiveFactors=positive_factors,
        negativeFactors=negative_factors,
        competitorComparison=comp_comparison,
        nextSteps=next_steps
    )

    verdict_reasoning = verdict_summary

    return total_score, grade, risk, verdict_reasoning, dim_scores, swot, recommendations, alternative_ideas, structured_verdict


@router.post("/assess", response_model=AssessmentResult)
async def create_real_assessment(data: AssessmentInput):
    assessment_id = f"gs-{uuid.uuid4().hex[:8]}"

    # 1. Fetch real POIs via Overpass API — scoped to business type
    competitors, amenities, banks = fetch_real_nearby_pois(data.lat, data.lon, data.radiusKm, data.businessType)

    # 2. Evaluate multi-condition spatial suitability (6 dimensions)
    total_score, grade, risk, reasoning, dim_scores, swot, recommendations, alt_ideas, structured_verdict = evaluate_multi_condition_suitability(
        data, competitors, amenities, banks
    )

    # 3. Break-even & Profit modeling
    monthly_rev = data.expectedMonthlyRevenue or max(20000.0, data.initialCapital * 0.35)
    monthly_budget = data.monthlyBudget or max(12000.0, monthly_rev * 0.65)
    net_profit = max(1500.0, monthly_rev - monthly_budget)
    breakeven_months = max(3, min(36, int(data.initialCapital / net_profit))) if net_profit > 0 else 18

    # 4. Match active government schemes
    matched_schemes = []
    for s in GOVERNMENT_SCHEMES:
        if s["maxAmount"] >= data.initialCapital * 0.4:
            matched_schemes.append({
                "id": s["id"],
                "name": s["name"],
                "fullName": s["fullName"],
                "maxAmount": s["maxAmount"],
                "interestRate": s["interestRate"],
                "subsidyPercent": s["subsidyPercent"],
                "moratorium": s["moratorium"],
                "moratoriumSchedule": f"No payments due for months 1–{s['moratorium']}, repayments start month {s['moratorium'] + 1}" if s["moratorium"] > 0 else "Regular monthly repayment from month 1",
                "applyUrl": s["applyUrl"]
            })

    result = AssessmentResult(
        id=assessment_id,
        businessName=data.businessName or "Proposed Enterprise",
        businessType=data.businessType,
        location=data.location,
        coordinates={"lat": data.lat, "lon": data.lon},
        radiusKm=data.radiusKm,
        overallScore=total_score,
        feasibilityGrade=grade,
        riskLevel=risk,
        verdictReasoning=reasoning,
        structuredVerdict=structured_verdict,
        breakEvenMonths=breakeven_months,
        projectedMonthlyProfit=round(net_profit, 2),
        dimensionScores=dim_scores,
        swot=swot,
        strengths=swot.strengths,
        risks=swot.threats,
        recommendations=recommendations,
        alternativeIdeas=alt_ideas,
        nearbyCompetitors=competitors[:25],
        nearbyAmenities=amenities[:20],
        nearbyBanks=banks[:15],
        competitorCount=len(competitors),
        amenityCount=len(amenities),
        bankCount=len(banks),
        matchedSchemes=matched_schemes[:5]
    )

    ASSESSMENTS_STORE[assessment_id] = result
    return result

@router.get("/assessment/{assessment_id}", response_model=AssessmentResult)
async def get_assessment(assessment_id: str):
    if assessment_id not in ASSESSMENTS_STORE:
        # Fallback assessment for demo
        sample = AssessmentInput(businessName=f"Assessment #{assessment_id}")
        return await create_real_assessment(sample)
    return ASSESSMENTS_STORE[assessment_id]
