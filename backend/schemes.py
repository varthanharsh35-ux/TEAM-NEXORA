"""Offline, source-backed screening. Eligibility is not a loan sanction."""

from copy import deepcopy
from datetime import date
import json
import math
from pathlib import Path

from intelligence import sector_prefix

CATALOG = json.loads(
    (Path(__file__).resolve().parents[1] / "data/scheme_catalog.json").read_text(encoding="utf-8")
)
ALIASES = {
    "income": ("household_income",),
    "sector": ("category",),
    "stage": ("business_stage",),
    "area": ("rural_urban", "urban_rural", "residence_type"),
}
ENUM_ALIASES = {
    "community": {"bc": "obc", "mbc": "obc", "scheduled caste": "sc", "scheduled tribe": "st"},
    "gender": {"woman": "female", "women": "female", "man": "male"},
    "state": {"tn": "tamil nadu", "tamil_nadu": "tamil nadu"},
    "sector": {
        "service": "services", "retail": "trading", "shop": "trading", "grocery": "trading",
        "dairy": "allied_agriculture", "poultry": "allied_agriculture", "fishing": "allied_agriculture",
        "beekeeping": "allied_agriculture", "weaving": "manufacturing", "handicrafts": "manufacturing",
        "repair": "services", "tailoring": "services", "agri": "agriculture",
    },
    "stage": {"existing": "expansion", "startup": "new", "greenfield": "new"},
    "education": {"8th": "class_8", "10th": "class_10", "12th": "class_12", "hsc": "class_12"},
}
# School attainment is deliberately not inferred from an ITI/diploma qualification.
EDUCATION = {"none": 0, "class_5": 5, "class_8": 8, "class_10": 10, "class_12": 12,
             "graduate": 12, "degree": 12, "postgraduate": 12}
NUMERIC_FIELDS = {
    "age", "income", "project_cost", "loan_amount", "tn_residence_years", "shg_obc_percentage"
}
BOOLEAN_FIELDS = {
    "extended_gestation", "weaker_section", "shg_member", "sanitation_worker_or_dependant",
    "person_with_disability", "prior_government_subsidy", "family_already_assisted",
    "has_capital_expenditure", "pmegp_activity_permitted", "microenterprise", "ex_serviceman",
    "first_generation", "self_financed",
}


def _normalise(data):
    values = dict(data)
    for field, aliases in ALIASES.items():
        if values.get(field) is None:
            for alias in aliases:
                if values.get(alias) is not None:
                    values[field] = values[alias]
                    break
    invalid = set()
    for field, value in list(values.items()):
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ("", "unspecified", "unknown", "prefer_not_to_say"):
                value = None
            else:
                if field == "sector":
                    # Dropdown sends a taxonomy sector id or dotted activity id
                    # (e.g. "retail.grocery"); reduce to the bare sector id only --
                    # do NOT collapse allied_agriculture into agriculture here, the
                    # ENUM_ALIASES table below depends on keeping them distinct.
                    value = sector_prefix(value)
                value = ENUM_ALIASES.get(field, {}).get(value, value)
        if value is not None and field in NUMERIC_FIELDS:
            try:
                if isinstance(value, bool):
                    raise ValueError
                value = float(value)
                if not math.isfinite(value) or value < 0:
                    raise ValueError
                if field in ("project_cost", "loan_amount") and value == 0:
                    raise ValueError
            except (ValueError, TypeError):
                invalid.add(field)
                value = None
        if value is not None and field in BOOLEAN_FIELDS:
            if value in ("true", "false"):
                value = value == "true"
            elif not isinstance(value, bool):
                invalid.add(field)
                value = None
        values[field] = value
    return values, invalid


def _condition(condition, values):
    """Return (True/False/None, missing fields) using three-valued logic."""
    if "not" in condition:
        verdict, missing = _condition(condition["not"], values)
        return (None if verdict is None else not verdict), missing
    for operator in ("all", "any"):
        if operator in condition:
            results = [_condition(child, values) for child in condition[operator]]
            decisive = False if operator == "all" else True
            if any(result[0] is decisive for result in results):
                return decisive, set()
            missing = set().union(*(result[1] for result in results))
            if any(result[0] is None for result in results):
                return None, missing
            return not decisive, set()
    field = condition["field"]
    actual = values.get(field)
    if actual is None:
        return None, {field}
    expected = condition["value"]
    op = condition["op"]
    operations = {
        "eq": lambda: actual == expected,
        "in": lambda: actual in expected,
        "gt": lambda: actual > expected,
        "gte": lambda: actual >= expected,
        "lte": lambda: actual <= expected,
    }
    try:
        return operations[op](), set()
    except TypeError:
        return None, {field}


def _screen_one(original, values, invalid):
    item = deepcopy(original)
    item.update(status="need_details", reasons=[], missing=[])
    if item.get("withdrawn_on"):
        item.update(status="withdrawn", reasons=["reasons.scheme_withdrawn"])
        return item

    eligibility = item["eligibility"]
    reasons, missing = set(), set()
    confirmation = False

    def check(field, allowed, reason=None):
        if allowed is None or allowed == "any":
            return
        actual = values.get(field)
        if actual is None:
            missing.add(field)
        else:
            aliases = ENUM_ALIASES.get(field, {})
            allowed_list = allowed if isinstance(allowed, list) else [allowed]
            allowed_norm = [aliases.get(a.strip().lower() if isinstance(a, str) else a, a) for a in allowed_list]
            if actual not in allowed_norm:
                reasons.add(reason or "reasons." + field + "_mismatch")

    def bound(field, lower=None, upper=None, exclusive=False, prefix=None):
        if lower is None and upper is None:
            return
        actual = values.get(field)
        if actual is None:
            missing.add(field)
            return
        prefix = prefix or field
        if lower is not None and (actual < lower or (exclusive and actual == lower)):
            reasons.add("reasons." + prefix + "_below_min")
        if upper is not None and actual > upper:
            reasons.add("reasons." + prefix + "_above_max")

    for field in ("community", "gender", "stage", "state"):
        check(field, eligibility.get(field))

    sectors = eligibility.get("sectors")
    if isinstance(sectors, dict):
        if values.get("sector") is None:
            missing.add("sector")
        elif values["sector"] in sectors.get("excluded", []):
            reasons.add("reasons.sector_mismatch")
    else:
        check("sector", sectors)

    age = eligibility["age"]
    for option in eligibility.get("age_options", []):
        verdict, absent = _condition(option["when"], values)
        if verdict is True:
            age["max"] = option["max"]
            item["unverified"] = [p for p in item["unverified"] if p != "eligibility.age.max"]
        elif verdict is None:
            missing.update(absent)
    bound("age", age.get("min"), age.get("max"), age.get("min_exclusive", False))

    rural, urban = (eligibility.get("income_limit_" + area) for area in ("rural", "urban"))
    if rural is not None or urban is not None:
        if rural == urban:
            limit = rural
        elif values.get("area") in ("rural", "urban"):
            limit = eligibility["income_limit_" + values["area"]]
        else:
            missing.add("area")
            limit = None
        if values.get("income") is None:
            missing.add("income")
        elif limit is not None:
            if values["income"] > limit:
                reasons.add("reasons.income_above")
            elif values["income"] == limit and eligibility.get("income_boundary_uncertain"):
                confirmation = True

    terms = item["terms"]
    bound("project_cost", terms.get("project_min"), terms.get("project_max"),
          eligibility.get("project_min_exclusive", False), "project")
    # Loan bands are NOT project-cost limits. Never infer loan = project or multiply savings here.
    bound("loan_amount", eligibility.get("loan_min"), terms.get("loan_cap"),
          eligibility.get("loan_min_exclusive", False), "loan")

    education = eligibility.get("education")
    if education and education != "any":
        minimum = education.get("minimum")
        for requirement in education.get("rules", []):
            verdict, absent = _condition(requirement["when"], values)
            if verdict is True:
                minimum = requirement["minimum"]
            elif verdict is None:
                missing.update(absent)
        if minimum:
            actual = values.get("education")
            if actual is None:
                missing.add("education")
            elif actual not in EDUCATION:
                confirmation = True
            elif EDUCATION[actual] < EDUCATION[minimum]:
                reasons.add("reasons.education_mismatch")

    for requirement in eligibility.get("requirements", []):
        verdict, absent = _condition(requirement, values)
        if verdict is None:
            missing.update(absent)
        elif verdict is False:
            reasons.add("reasons." + requirement.get("field", "target_group") + "_mismatch")

    for option in item.get("term_options", []):
        verdict, _ = _condition(option["when"], values)
        if verdict is True:
            terms.update(option["terms"])
            resolved = {"terms." + key for key in option["terms"]}
            item["unverified"] = [p for p in item["unverified"] if p not in resolved]

    # An unpublished eligibility rule is an agency question, not a fabricated unlimited allowance.
    confirmation |= any(p.startswith("eligibility.") for p in item["unverified"])
    confirmation |= "availability_confirmed" in item["unverified"]
    if invalid:
        missing.update(invalid)
    if reasons:
        item["status"] = "not_eligible"
    elif missing or confirmation:
        item["status"] = "need_details"
    else:
        item["status"] = "eligible"
    if confirmation:
        reasons.add("reasons.confirm_with_agency")
    if invalid:
        reasons.add("reasons.invalid_input")
    if missing:
        reasons.add("reasons.details_required")
    item["reasons"] = sorted(reasons)
    item["missing"] = sorted(missing)
    return item


def screen(data):
    """Screen an individual profile without network calls or generated financial figures.

    Missing project cost remains missing; margin alone cannot establish the cost of a business.
    Fields absent from the published criteria remain null and require agency confirmation.
    """
    values, invalid = _normalise(data)
    verified = CATALOG["checked"]
    next_check = CATALOG["next_check"]
    return {
        "schemes": [_screen_one(item, values, invalid) for item in CATALOG["schemes"]],
        "freshness": {
            "dataset": "schemes",
            "version": verified,
            "last_verified": verified,
            "next_check": next_check,
            "status": "stale" if date.today().isoformat() > next_check else "fresh",
        },
    }
