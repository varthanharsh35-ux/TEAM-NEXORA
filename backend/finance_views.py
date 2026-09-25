"""Task 3.6: Split finance into three focused routes.

The single /api/finance endpoint stays untouched (rule: keep the existing
maths).  Three new routes slice the same calculation into the views the
UI needs, each with a traffic-light verdict at the top:

  POST /api/finance/overview   — project cost, scheme, loan, gap, verdict
  POST /api/finance/allocation — how margin + loan + gap fill the project
  POST /api/finance/repayment  — schedule, EMI, moratorium, totals, verdict

Every number comes from finance.calculate() — nothing is re-derived.
"""

from finance import calculate, money


def _verdict(checks):
    """Traffic-light verdict: green / amber / red with a one-sentence reason.

    green  = all checks pass — go ahead
    amber  = minor gap or caution — proceed with awareness
    red    = blocker — cannot proceed as stated
    """
    if checks.get("blocker"):
        return {
            "light": "red",
            "label": "blocker",
            "reason_key": checks["blocker_reason_key"],
            "reason_params": checks.get("blocker_params", {}),
        }
    if checks.get("caution"):
        return {
            "light": "amber",
            "label": "caution",
            "reason_key": checks["caution_reason_key"],
            "reason_params": checks.get("caution_params", {}),
        }
    return {
        "light": "green",
        "label": "go",
        "reason_key": "verdict.finance.all_clear",
        "reason_params": {},
    }


def overview(margin, start_date=None, scheme_id="auto", project_cost=None,
             activity_id=None):
    """High-level finance summary with verdict."""
    result = calculate(margin, start_date, scheme_id, project_cost)

    checks = {}
    gap = result.get("funding_gap", 0)
    if result.get("scheme") == "outside":
        checks["blocker"] = True
        checks["blocker_reason_key"] = "verdict.finance.outside_scheme_range"
        checks["blocker_params"] = {"project_cost": result["project_cost"]}
    elif result.get("cap_applied"):
        checks["caution"] = True
        checks["caution_reason_key"] = "verdict.finance.cap_applied"
        checks["caution_params"] = {
            "loan": result["loan"],
            "maximum_loan": result["maximum_loan"],
        }
    elif gap > 0:
        checks["blocker"] = True
        checks["blocker_reason_key"] = "verdict.finance.funding_gap"
        checks["blocker_params"] = {"gap": gap}

    return {
        "margin": result["margin"],
        "project_cost": result["project_cost"],
        "scheme": result.get("scheme", ""),
        "loan": result.get("loan", 0),
        "maximum_loan": result.get("maximum_loan", 0),
        "funding_gap": gap,
        "cap_applied": result.get("cap_applied", False),
        "annual_rate": result.get("annual_rate", 0),
        "tenure_months": result.get("tenure_months", 0),
        "moratorium_months": result.get("moratorium_months", 0),
        "verdict": _verdict(checks),
        "assumptions": [
            {
                "key": "assumptions.simple_interest_capitalised_once",
                "confirm_with": "sanctioning_agency",
            },
        ],
    }


def allocation(margin, start_date=None, scheme_id="auto", project_cost=None,
               activity_id=None, facilities_owned=None):
    """How margin, loan and any gap fill the project cost.

    If an activity_id is provided, includes the inventory breakdown.
    """
    result = calculate(margin, start_date, scheme_id, project_cost)

    margin_share = result["margin"]
    loan_share = result.get("loan", 0)
    gap = result.get("funding_gap", 0)
    total = result["project_cost"]

    # Proportions
    margin_pct = round(margin_share / total * 100, 1) if total > 0 else 0
    loan_pct = round(loan_share / total * 100, 1) if total > 0 else 0
    gap_pct = round(gap / total * 100, 1) if total > 0 else 0

    # Inventory plan if activity specified
    inventory_summary = None
    if activity_id:
        try:
            from inventory import plan as inv_plan
            inventory_summary = inv_plan(
                activity_id,
                facilities_owned=facilities_owned or [],
            )
        except Exception:
            inventory_summary = None

    checks = {}
    if gap > 0:
        checks["blocker"] = True
        checks["blocker_reason_key"] = "verdict.allocation.funding_gap"
        checks["blocker_params"] = {"gap": gap, "gap_pct": gap_pct}
    elif margin_pct < 10:
        checks["caution"] = True
        checks["caution_reason_key"] = "verdict.allocation.low_margin_share"
        checks["caution_params"] = {"margin_pct": margin_pct}

    alloc = {
        "project_cost": total,
        "margin": margin_share,
        "margin_pct": margin_pct,
        "loan": loan_share,
        "loan_pct": loan_pct,
        "funding_gap": gap,
        "gap_pct": gap_pct,
        "scheme": result.get("scheme", ""),
        "verdict": _verdict(checks),
    }

    if inventory_summary:
        alloc["inventory"] = inventory_summary

    return alloc


def repayment(margin, start_date=None, scheme_id="auto", project_cost=None):
    """Full repayment schedule with verdict."""
    result = calculate(margin, start_date, scheme_id, project_cost)

    schedule = result.get("schedule", [])
    quarterly_payment = result.get("quarterly_payment", 0)
    total_interest = result.get("total_interest", 0)
    total_repayment = result.get("total_repayment", 0)
    moratorium_interest = result.get("moratorium_interest", 0)
    loan = result.get("loan", 0)
    rate = result.get("annual_rate", 0)
    tenure = result.get("tenure_months", 0)
    moratorium = result.get("moratorium_months", 0)

    # Monthly EMI equivalent for affordability display
    monthly_equivalent = round(quarterly_payment / 3, 2) if quarterly_payment else 0

    # Moratorium quarters
    moratorium_quarters = [s for s in schedule if s.get("moratorium")]
    repayment_quarters = [s for s in schedule if not s.get("moratorium")]

    checks = {}
    if loan == 0 and result.get("scheme") == "outside":
        checks["blocker"] = True
        checks["blocker_reason_key"] = "verdict.repayment.no_loan"
        checks["blocker_params"] = {}
    elif loan == 0:
        # Self-funded — no repayment needed, green
        pass
    elif total_interest > loan * 0.5:
        checks["caution"] = True
        checks["caution_reason_key"] = "verdict.repayment.high_interest_ratio"
        checks["caution_params"] = {
            "interest": total_interest,
            "loan": loan,
            "ratio_pct": round(total_interest / loan * 100, 1) if loan > 0 else 0,
        }

    return {
        "loan": loan,
        "annual_rate": rate,
        "tenure_months": tenure,
        "moratorium_months": moratorium,
        "quarterly_payment": quarterly_payment,
        "monthly_equivalent": monthly_equivalent,
        "moratorium_interest": moratorium_interest,
        "total_interest": total_interest,
        "total_repayment": total_repayment,
        "moratorium_schedule": moratorium_quarters,
        "repayment_schedule": repayment_quarters,
        "schedule": schedule,
        "verdict": _verdict(checks),
        "assumptions": [
            {
                "key": "assumptions.simple_interest_capitalised_once",
                "confirm_with": "sanctioning_agency",
            },
            {
                "key": "assumptions.quarterly_reducing_balance",
                "confirm_with": "sanctioning_agency",
            },
        ],
    }
