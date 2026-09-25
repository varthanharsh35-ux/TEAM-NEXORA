import math
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from data.schemes_data import GOVERNMENT_SCHEMES
from routers.assessment import fetch_real_nearby_pois

router = APIRouter(tags=["Schemes"])

@router.get("/schemes")
async def list_schemes(
    category: Optional[str] = None,
    max_amount: Optional[float] = Query(None, alias="maxAmount"),
    community: Optional[str] = None,
    search: Optional[str] = None,
    business_type: Optional[str] = Query(None, alias="businessType")
):
    results = GOVERNMENT_SCHEMES

    # Category-scoped filtering: only show schemes applicable to the user's business type
    if business_type and business_type != "all":
        bt = business_type.lower()
        results = [s for s in results if bt in s.get("applicableSectors", []) or "all" in s.get("applicableSectors", [])]

    if category and category != "all":
        results = [s for s in results if s["category"].lower() == category.lower()]

    if max_amount:
        results = [s for s in results if s["maxAmount"] >= max_amount]

    if community and community != "all":
        results = [s for s in results if "all" in s.get("community", []) or community.lower() in [c.lower() for c in s.get("community", [])]]

    if search:
        q = search.lower()
        results = [
            s for s in results
            if q in s["name"].lower() or q in s["fullName"].lower() or q in s["eligibility"].lower()
        ]

    # Enrich with explicit moratorium schedules
    enriched = []
    for s in results:
        mor = s.get("moratorium", 0)
        mor_text = f"No payments due for months 1–{mor}, payments start month {mor + 1}" if mor > 0 else "Repayments start immediately from month 1"
        enriched.append({
            **s,
            "moratoriumSchedule": mor_text
        })

    return {
        "count": len(enriched),
        "schemes": enriched
    }

@router.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str):
    scheme = next((s for s in GOVERNMENT_SCHEMES if s["id"] == scheme_id or s["name"].lower() == scheme_id.lower()), None)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    mor = scheme.get("moratorium", 0)
    return {
        **scheme,
        "moratoriumSchedule": f"No payments due for months 1–{mor}, payments start month {mor + 1}" if mor > 0 else "Repayments start immediately from month 1"
    }

@router.get("/schemes/calculator/bidirectional")
@router.get("/schemes/{scheme_id}/emi")
async def calculate_bidirectional_emi(
    scheme_id: Optional[str] = "custom",
    principal: Optional[float] = None,
    tenure_months: Optional[int] = Query(None, alias="tenure"),
    custom_rate: Optional[float] = Query(None, alias="rate"),
    desired_emi: Optional[float] = Query(None, alias="desiredEmi"),
    start_date: Optional[str] = Query(None, alias="startDate")
):
    scheme = next((s for s in GOVERNMENT_SCHEMES if s["id"] == scheme_id or s["name"].lower() == scheme_id.lower()), None)

    P = principal if principal is not None else (scheme["maxAmount"] if scheme else 50000.0)
    R_annual = custom_rate if custom_rate is not None else (scheme["interestRate"] if scheme else 9.5)
    r = (R_annual / 12.0) / 100.0

    # Parse start date or default to today
    if start_date:
        try:
            loan_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            loan_start = datetime.date.today()
    else:
        loan_start = datetime.date.today()

    if desired_emi and desired_emi > 0:
        # User specified target monthly EMI -> Calculate tenure (N)
        # N = -ln(1 - (P * r) / EMI) / ln(1 + r)
        min_possible_emi = P * r
        if desired_emi <= min_possible_emi:
            # Desired EMI cannot even cover interest
            N = 120
            emi = round(min_possible_emi * 1.05, 2)
        else:
            try:
                n_calc = -math.log(1 - (P * r) / desired_emi) / math.log(1 + r)
                N = max(1, min(120, int(math.ceil(n_calc))))
                emi = round(desired_emi, 2)
            except Exception:
                N = 36
                emi = round(desired_emi, 2)

        total_payment = round(emi * N, 2)
        total_interest = round(max(0.0, total_payment - P), 2)

    else:
        # Standard calculation: tenure given -> Calculate EMI
        N = tenure_months if tenure_months is not None else (scheme["tenure"] if scheme else 36)
        if N <= 0: N = 12
        if P <= 0: P = 10000.0

        if r == 0:
            emi = P / N
            total_interest = 0.0
        else:
            emi = (P * r * math.pow(1 + r, N)) / (math.pow(1 + r, N) - 1)
            total_payment = emi * N
            total_interest = total_payment - P

    # Projected clearance date from chosen start date
    moratorium = scheme.get("moratorium", 0) if scheme else 0
    total_months = N + moratorium
    est_completion_date = loan_start + datetime.timedelta(days=int(total_months * 30.4))

    # First payment date (after moratorium)
    first_payment_date = loan_start + datetime.timedelta(days=int((moratorium + 1) * 30.4))

    return {
        "schemeId": scheme_id,
        "schemeName": scheme["name"] if scheme else "Custom Loan",
        "principal": round(P, 2),
        "interestRateAnnual": R_annual,
        "tenureMonths": N,
        "monthlyEMI": round(emi, 2),
        "totalInterest": round(total_interest, 2),
        "totalRepayment": round(P + total_interest, 2),
        "moratoriumMonths": moratorium,
        "moratoriumSchedule": f"No payments due for months 1–{moratorium}. Your first payment begins in month {moratorium + 1}." if moratorium > 0 else "Regular monthly repayment from month 1.",
        "loanStartDate": loan_start.strftime("%Y-%m-%d"),
        "firstPaymentDate": first_payment_date.strftime("%B %d, %Y"),
        "projectedCompletionDate": est_completion_date.strftime("%B %Y"),
        "dateFramingStatement": f"If you start on {loan_start.strftime('%B %d, %Y')}, your loan will be fully repaid by {est_completion_date.strftime('%B %d, %Y')}.",
        "eligibleSubsidy": round(P * (scheme.get("subsidyPercent", 0) / 100.0), 2) if scheme else 0.0
    }

@router.get("/financial-institutions")
async def list_nearby_financial_institutions(
    lat: float = Query(20.7453),
    lon: float = Query(78.6022),
    radius_km: float = Query(5.0, alias="radiusKm")
):
    _, _, banks = fetch_real_nearby_pois(lat, lon, radius_km)
    return {
        "count": len(banks),
        "institutions": banks
    }
