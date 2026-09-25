"""Debt portfolio and loan tracking engine."""

import datetime
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

from finance import monthly_emi, add_months

from storage import database_path
DB_PATH = database_path('tracker.sqlite3')

FACILITY_TYPES = {"term_loan", "mudra", "overdraft", "cc", "informal"}
STATUSES = {"active", "closed", "npa"}


def _get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                lender TEXT NOT NULL,
                facility_type TEXT NOT NULL,
                status TEXT NOT NULL,
                principal REAL NOT NULL,
                annual_rate REAL NOT NULL,
                tenure_months INTEGER NOT NULL,
                grace_months INTEGER NOT NULL,
                disbursement_date TEXT NOT NULL,
                emi REAL NOT NULL,
                outstanding_balance REAL NOT NULL,
                next_due_date TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_loans_user ON loans (user_id)")
    return conn


def _validate_date(d_str: str) -> datetime.date:
    if not isinstance(d_str, str):
        raise ValueError("invalid_date")
    try:
        return datetime.date.fromisoformat(d_str)
    except Exception:
        raise ValueError("invalid_date")


def add_loan(
    user_id: str,
    lender: str,
    facility_type: str,
    status: str,
    principal: float,
    annual_rate: float,
    tenure_months: int,
    disbursement_date: str,
    grace_months: int = 0
) -> dict:
    """Record a debt facility in the portfolio."""
    if not user_id or not isinstance(user_id, str):
        raise ValueError("invalid_user_id")
    if not lender or not isinstance(lender, str):
        raise ValueError("invalid_lender")

    fac = (facility_type or "").strip().lower()
    if fac not in FACILITY_TYPES:
        raise ValueError("invalid_facility_type")

    st = (status or "").strip().lower()
    if st not in STATUSES:
        raise ValueError("invalid_status")

    try:
        p = float(principal)
        r = float(annual_rate)
        t = int(tenure_months)
        g = int(grace_months)
        if p <= 0 or r < 0 or t <= 0 or g < 0 or t <= g:
            raise ValueError("invalid_terms")
    except (TypeError, ValueError):
        raise ValueError("invalid_terms")

    disb_d = _validate_date(disbursement_date)

    repay_tenure = t - g
    # CRITICAL: Always use monthly_emi from finance.py, never reimplement
    calc_emi = float(monthly_emi(p, r / 100.0, repay_tenure))

    # Next due date is first repayment after grace period
    first_due = add_months(disb_d, g + 1).isoformat()
    outstanding = p if st != "closed" else 0.0
    loan_id = str(uuid.uuid4())

    with closing(_get_connection()) as conn:
        with conn:
            conn.execute(
                """INSERT INTO loans (
                    id, user_id, lender, facility_type, status, principal,
                    annual_rate, tenure_months, grace_months, disbursement_date,
                    emi, outstanding_balance, next_due_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (loan_id, user_id, lender.strip(), fac, st, p, r, t, g,
                 disbursement_date, calc_emi, outstanding, first_due)
            )

    return {
        "id": loan_id,
        "user_id": user_id,
        "lender": lender.strip(),
        "facility_type": fac,
        "status": st,
        "principal": round(p, 2),
        "annual_rate": round(r, 2),
        "tenure_months": t,
        "grace_months": g,
        "disbursement_date": disbursement_date,
        "emi": round(calc_emi, 2),
        "outstanding_balance": round(outstanding, 2),
        "next_due_date": first_due
    }


def list_loans(user_id: str) -> dict:
    """Return all loans and portfolio obligations for a user."""
    if not user_id:
        raise ValueError("invalid_user_id")

    loans = []
    tot_outstanding = 0.0
    tot_monthly_emi = 0.0

    with closing(_get_connection()) as conn:
        cur = conn.execute(
            """SELECT id, lender, facility_type, status, principal, annual_rate,
                      tenure_months, disbursement_date, emi, outstanding_balance, next_due_date
               FROM loans WHERE user_id = ? ORDER BY disbursement_date DESC""",
            (user_id,)
        )
        for r in cur.fetchall():
            st = r[3]
            emi = float(r[8])
            bal = float(r[9])

            if st == "active":
                tot_monthly_emi += emi
                tot_outstanding += bal
            elif st == "npa":
                tot_outstanding += bal

            loans.append({
                "id": r[0],
                "lender": r[1],
                "facility_type": r[2],
                "status": st,
                "principal": round(float(r[4]), 2),
                "annual_rate": round(float(r[5]), 2),
                "tenure_months": int(r[6]),
                "disbursement_date": r[7],
                "emi": round(emi, 2),
                "outstanding_balance": round(bal, 2),
                "next_due_date": r[10]
            })

    return {
        "loans": loans,
        "portfolio_totals": {
            "total_outstanding": round(tot_outstanding, 2),
            "monthly_emi_obligation": round(tot_monthly_emi, 2)
        }
    }


def close_loan(user_id: str, loan_id: str) -> bool:
    """Mark a loan as closed and set outstanding balance to 0."""
    if not user_id or not loan_id:
        return False
    with closing(_get_connection()) as conn:
        with conn:
            cur = conn.execute(
                "UPDATE loans SET status = 'closed', outstanding_balance = 0.0 WHERE id = ? AND user_id = ?",
                (loan_id, user_id)
            )
            return cur.rowcount > 0


if __name__ == "__main__":
    test_user = "user_debt_" + str(uuid.uuid4())[:8]

    # 1. Add active term loan
    l1 = add_loan(
        user_id=test_user,
        lender="State Bank of India",
        facility_type="term_loan",
        status="active",
        principal=100000.0,
        annual_rate=12.0,
        tenure_months=12,
        disbursement_date="2026-01-01",
        grace_months=0
    )
    assert l1["facility_type"] == "term_loan"
    assert l1["status"] == "active"
    assert l1["principal"] == 100000.0
    # Expected EMI for 100k at 12% for 12m from monthly_emi
    expected_emi = float(monthly_emi(100000, 0.12, 12))
    assert abs(l1["emi"] - expected_emi) < 0.01

    # 2. Add second loan (MUDRA) with grace period
    l2 = add_loan(
        user_id=test_user,
        lender="Canara Bank",
        facility_type="mudra",
        status="active",
        principal=50000.0,
        annual_rate=9.0,
        tenure_months=24,
        disbursement_date="2026-02-01",
        grace_months=3
    )
    assert l2["facility_type"] == "mudra"
    expected_mudra_emi = float(monthly_emi(50000, 0.09, 21))
    assert abs(l2["emi"] - expected_mudra_emi) < 0.01

    # 3. List loans computes portfolio totals
    portfolio = list_loans(test_user)
    assert len(portfolio["loans"]) == 2
    assert portfolio["portfolio_totals"]["total_outstanding"] == 150000.0
    expected_tot_emi = round(expected_emi + expected_mudra_emi, 2)
    assert abs(portfolio["portfolio_totals"]["monthly_emi_obligation"] - expected_tot_emi) < 0.02

    # 4. Close loan updates status and reduces EMI obligation
    closed = close_loan(test_user, l1["id"])
    assert closed is True
    p2 = list_loans(test_user)
    assert p2["portfolio_totals"]["total_outstanding"] == 50000.0
    assert abs(p2["portfolio_totals"]["monthly_emi_obligation"] - round(expected_mudra_emi, 2)) < 0.01

    # 5. Closing non-existent loan returns False
    assert close_loan(test_user, "non_existent") is False

    # 6. Invalid facility type raises ValueError
    try:
        add_loan(test_user, "Bank", "unsupported_facility", "active", 10000, 10, 12, "2026-01-01")
        assert False, "Should fail on invalid facility type"
    except ValueError:
        pass

    # 7. Invalid status raises ValueError
    try:
        add_loan(test_user, "Bank", "term_loan", "pending_approval", 10000, 10, 12, "2026-01-01")
        assert False, "Should fail on invalid status"
    except ValueError:
        pass

    # 8. Grace period >= tenure raises ValueError
    try:
        add_loan(test_user, "Bank", "term_loan", "active", 10000, 10, 12, "2026-01-01", grace_months=12)
        assert False, "Should fail when grace >= tenure"
    except ValueError:
        pass

    # Clean up test loans
    with closing(_get_connection()) as conn:
        with conn:
            conn.execute("DELETE FROM loans WHERE user_id = ?", (test_user,))

    print("All 8+ debt engine tests passed successfully!")
