from fastapi import APIRouter
from models import FinancialPlanInput, FinancialPlanResult, CashflowInput, CashflowResult, CashflowMonthDetail

router = APIRouter(prefix="/financial", tags=["Financial"])

SECTOR_PROFILES = {
    "retail": {"min": 50000, "established": 300000, "rentRatio": 0.02, "invRatio": 0.35, "staffRatio": 0.05, "utilRatio": 0.015, "margin": 22.0},
    "food": {"min": 75000, "established": 450000, "rentRatio": 0.03, "invRatio": 0.30, "staffRatio": 0.08, "utilRatio": 0.025, "margin": 28.0},
    "agriculture": {"min": 40000, "established": 250000, "rentRatio": 0.01, "invRatio": 0.40, "staffRatio": 0.06, "utilRatio": 0.02, "margin": 25.0},
    "handicraft": {"min": 25000, "established": 150000, "rentRatio": 0.01, "invRatio": 0.35, "staffRatio": 0.04, "utilRatio": 0.01, "margin": 32.0},
    "textile": {"min": 60000, "established": 350000, "rentRatio": 0.02, "invRatio": 0.38, "staffRatio": 0.06, "utilRatio": 0.015, "margin": 24.0},
    "dairy": {"min": 80000, "established": 500000, "rentRatio": 0.015, "invRatio": 0.35, "staffRatio": 0.07, "utilRatio": 0.02, "margin": 20.0},
    "services": {"min": 35000, "established": 200000, "rentRatio": 0.02, "invRatio": 0.20, "staffRatio": 0.05, "utilRatio": 0.02, "margin": 35.0},
    "manufacturing": {"min": 150000, "established": 800000, "rentRatio": 0.025, "invRatio": 0.40, "staffRatio": 0.10, "utilRatio": 0.035, "margin": 26.0},
    "transport": {"min": 100000, "established": 600000, "rentRatio": 0.01, "invRatio": 0.15, "staffRatio": 0.12, "utilRatio": 0.04, "margin": 22.0},
    "other": {"min": 50000, "established": 300000, "rentRatio": 0.02, "invRatio": 0.30, "staffRatio": 0.05, "utilRatio": 0.02, "margin": 25.0},
}

@router.post("/plan", response_model=FinancialPlanResult)
async def generate_financial_plan(data: FinancialPlanInput):
    inv = data.investmentAmount
    btype = data.businessType.lower()
    profile = SECTOR_PROFILES.get(btype, SECTOR_PROFILES["retail"])

    # Capital allocation formula tailored for rural MSMEs
    equipment_capex = round(inv * 0.45, 2)
    initial_inventory = round(inv * profile["invRatio"], 2)
    contingency = round(inv * (data.contingencyReservePercent / 100.0), 2)
    working_capital = round(max(5000.0, inv - (equipment_capex + initial_inventory + contingency)), 2)

    # Monthly recurring expenses
    rent = round(inv * profile["rentRatio"], 2)
    stock_replenish = round(inv * (profile["invRatio"] * 0.3), 2)
    staff = round(inv * profile["staffRatio"], 2)
    utilities = round(inv * profile["utilRatio"], 2)
    marketing = round(inv * 0.01, 2)
    monthly_expenses = data.monthlyExpenses or (rent + stock_replenish + staff + utilities + marketing)

    # Runway estimation
    runway = int(working_capital / monthly_expenses) if monthly_expenses > 0 else 12

    # Profit & break-even calculation
    operating_margin = data.expectedMarginPercent or profile["margin"]
    projected_monthly_revenue = monthly_expenses / (1.0 - (operating_margin / 100.0)) if operating_margin < 100 else monthly_expenses * 1.3
    monthly_net_profit = projected_monthly_revenue - monthly_expenses
    breakeven_months = max(3, int(inv / monthly_net_profit)) if monthly_net_profit > 0 else 18
    break_even_units = int(monthly_expenses / 350) if monthly_expenses > 0 else 40

    # ROI months
    roi_months = breakeven_months

    health_score = 75
    if runway >= 3: health_score += 10
    if inv >= profile["min"]: health_score += 10
    health_score = min(98, health_score)

    monthly_projection = []
    base_rev = projected_monthly_revenue
    for m in range(1, 13):
        ramp = min(1.3, 0.4 + (m * 0.08))
        rev = round(base_rev * ramp, 2)
        exp = round(monthly_expenses * (0.85 + (m * 0.02)), 2)
        monthly_projection.append({
            "month": f"M{m}",
            "revenue": rev,
            "expenses": exp,
            "profit": round(rev - exp, 2)
        })

    recommendations = [
        f"Maintain ₹{contingency:,.0f} strictly in an emergency liquid account for seasonal lean periods.",
        "Negotiate 15-day supplier credit for recurring inventory restocking to preserve working capital.",
        f"Target at least ₹{projected_monthly_revenue:,.0f}/month revenue to achieve full break-even in ~{breakeven_months} months."
    ]

    return FinancialPlanResult(
        capitalBreakdown={
            "machineryAndEquipment": equipment_capex,
            "initialInventoryStock": initial_inventory,
            "workingCapitalBuffer": working_capital,
            "emergencyReserve": contingency
        },
        bareMinimumCapital=float(profile["min"]),
        establishedCapital=float(profile["established"]),
        averageSetupCost=round(inv * 0.75, 2),
        runwayMonths=max(1, runway),
        breakEvenMonths=breakeven_months,
        breakEvenUnitsMonthly=break_even_units,
        operatingMargin=operating_margin,
        returnOnInvestmentMonths=max(3, roi_months),
        financialHealthScore=health_score,
        monthlyRecurring={
            "rent": rent,
            "inventory": stock_replenish,
            "staff": staff,
            "utilities": utilities,
            "marketing": marketing
        },
        monthlyProjection=monthly_projection,
        recommendations=recommendations
    )

@router.post("/cashflow", response_model=CashflowResult)
async def simulate_cashflow(data: CashflowInput):
    balance = data.initialBalance
    breakdown = []
    lowest_balance = balance
    peak_cash = balance
    peak_month = 1
    total_outflow = 0.0

    inflows = data.monthlyInflows if len(data.monthlyInflows) >= data.months else [45000.0] * data.months
    outflows = data.monthlyOutflows if len(data.monthlyOutflows) >= data.months else [32000.0] * data.months

    for m in range(1, data.months + 1):
        inf = inflows[m - 1] if m - 1 < len(inflows) else 45000.0
        outf = outflows[m - 1] if m - 1 < len(outflows) else 32000.0
        net = inf - outf
        balance += net
        total_outflow += outf

        if balance < lowest_balance:
            lowest_balance = balance
        if balance > peak_cash:
            peak_cash = balance
            peak_month = m

        breakdown.append(CashflowMonthDetail(
            month=m,
            inflow=round(inf, 2),
            outflow=round(outf, 2),
            net=round(net, 2),
            endingBalance=round(balance, 2)
        ))

    avg_burn = round(total_outflow / data.months, 2)

    suggestions = [
        "Monitor months with lowest cash reserves to pre-arrange credit lines.",
        "Reinvest surplus cash from peak months into bulk discount inventory purchases.",
        "Incentivize upfront digital customer payments with 1-2% discounts."
    ]

    return CashflowResult(
        monthlyBreakdown=breakdown,
        lowestBalance=round(lowest_balance, 2),
        peakCashMonth=peak_month,
        averageBurnRate=avg_burn,
        isPositiveCashflow=lowest_balance > 0,
        suggestions=suggestions
    )
