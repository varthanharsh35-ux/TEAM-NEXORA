"""Deterministic SIH financial engine. Amounts rounded to paise, half up.

Assumption: simple interest accrues during moratorium and is capitalised once.
Quarterly reducing balance thereafter. Total tenure INCLUDES the moratorium.
This assumption must be confirmed by the sanctioning agency.
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date
import calendar

D = Decimal
def money(x):
    return D(str(x)).quantize(D('.01'), rounding=ROUND_HALF_UP)

def add_months(day, months):
    m = day.month - 1 + months
    y, m = day.year + m // 12, m % 12 + 1
    return date(y, m, min(day.day, calendar.monthrange(y, m)[1]))

def calculate(margin, start_date=None):
    try:
        raw = D(str(margin))
        if not raw.is_finite() or raw <= 0 or raw > 100000000:
            raise ValueError('invalid_margin')
        margin = money(raw)
        if margin <= 0: raise ValueError('invalid_margin')
    except (InvalidOperation, TypeError):
        raise ValueError('invalid_margin')
    start = date.fromisoformat(start_date) if start_date else date.today()
    project = money(margin / D('.10'))
    maximum = money(project * D('.90'))
    base = dict(margin=float(margin), project_cost=float(project), maximum_loan=float(maximum), start_date=start.isoformat())
    if project > 5000000:
        return dict(base, scheme='outside', loan=0, funding_gap=float(project-margin), schedule=[], quarterly_payment=0, total_interest=0, total_repayment=0, annual_rate=0, tenure_months=0, moratorium_months=0, cap_applied=False)
    micro = project <= 140000
    rate, tenure, moratorium, cap = (D('.065'),36,3,D(125000)) if micro else (D('.08'),84,6,D(4500000))
    loan = min(maximum, cap)
    accrued = money(loan * rate * D(moratorium) / 12)
    balance = loan
    schedule = []
    for month in range(3, moratorium+1, 3):
        interest = money(loan * rate / 4)
        # Simple interest across the whole grace period, never compounded here.
        closing = money(loan + loan * rate * D(month) / 12)
        schedule.append(dict(month=month, due_date=add_months(start,month).isoformat(), opening=float(balance), interest=float(interest), principal=0, payment=0, balance=float(closing), moratorium=True))
        balance = closing
    balance = loan + accrued
    n = (tenure - moratorium)//3
    q = rate / 4
    payment = money(balance*q/(1-(1+q)**(-n)))
    for k in range(1,n+1):
        interest = money(balance*q)
        paid = balance+interest if k==n else min(payment,balance+interest)
        principal = paid-interest
        closing = money(balance-principal)
        month=moratorium+k*3
        schedule.append(dict(month=month,due_date=add_months(start,month).isoformat(),opening=float(balance),interest=float(interest),principal=float(principal),payment=float(paid),balance=float(closing),moratorium=False))
        balance=closing
    total=sum((D(str(r['payment'])) for r in schedule),D(0))
    return dict(base,scheme='micro' if micro else 'term',loan=float(loan),funding_gap=float(project-margin-loan),cap_applied=loan<maximum,annual_rate=float(rate*100),tenure_months=tenure,moratorium_months=moratorium,quarterly_payment=float(payment),moratorium_interest=float(accrued),total_interest=float(total-loan),total_repayment=float(total),schedule=schedule)
