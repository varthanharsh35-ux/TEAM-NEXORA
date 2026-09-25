"""Cash flow and debt ledgers (docs/TASKS.md Task 2.8, docs/UX_FLOW.md 4.5 and 4.6).

Two rules shape this module:

1. Recorded transactions and forecasts never mix. Everything stored here is
   something the user actually says happened. Projections live in the report.
2. EMI is not re-derived. `finance.monthly_emi` owns that arithmetic, so the
   repayment figure on the debt page matches the one in the funding plan to
   the paise.
"""

import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from finance import money, monthly_emi

from storage import database_path
DB = database_path('ledger.sqlite3')

DIRECTIONS = ("in", "out")
STATUSES = ("on_track", "late", "closed")


@contextmanager
def db():
    connection = sqlite3.connect(DB, timeout=15)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS entries ("
                "id TEXT PRIMARY KEY, owner TEXT, entry_date TEXT, direction TEXT,"
                " category TEXT, amount REAL, note TEXT, created REAL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS loans ("
                "id TEXT PRIMARY KEY, owner TEXT, lender TEXT, facility TEXT, status TEXT,"
                " principal REAL, rate REAL, tenure INTEGER, emi REAL, balance REAL,"
                " principal_repaid REAL, start_date TEXT, scheme_id TEXT, created REAL)"
            )
            yield connection
    finally:
        connection.close()


def _check_date(value):
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_date")
    if not 2000 <= parsed.year <= 2100:
        raise ValueError("invalid_date")
    return parsed.isoformat()


def _check_amount(value, field="amount", allow_zero=False):
    try:
        amount = float(money(value))
    except Exception:
        raise ValueError(f"invalid_{field}")
    low = 0 if allow_zero else 0.000001
    if not low <= amount <= 100000000:
        raise ValueError(f"invalid_{field}")
    return amount


# --------------------------------------------------------------------- cash flow


def add_entry(owner, entry_date, direction, amount, category="", note=""):
    if direction not in DIRECTIONS:
        raise ValueError("invalid_direction")
    row = {
        "id": uuid.uuid4().hex,
        "owner": owner,
        "entry_date": _check_date(entry_date),
        "direction": direction,
        "category": str(category)[:60],
        "amount": _check_amount(amount),
        "note": str(note)[:200],
        "created": time.time(),
    }
    with db() as c:
        c.execute(
            "INSERT INTO entries VALUES (:id,:owner,:entry_date,:direction,:category,"
            ":amount,:note,:created)",
            row,
        )
    return row


def delete_entry(owner, entry_id):
    with db() as c:
        cursor = c.execute("DELETE FROM entries WHERE id=? AND owner=?", (entry_id, owner))
    return cursor.rowcount > 0


def entries(owner, start=None, end=None):
    query = "SELECT * FROM entries WHERE owner=?"
    params = [owner]
    if start:
        query += " AND entry_date>=?"
        params.append(_check_date(start))
    if end:
        query += " AND entry_date<=?"
        params.append(_check_date(end))
    with db() as c:
        rows = c.execute(query + " ORDER BY entry_date DESC, created DESC", params).fetchall()
    return [dict(r) for r in rows]


def cash_summary(owner, start=None, end=None):
    rows = entries(owner, start, end)
    inflow = float(money(sum(r["amount"] for r in rows if r["direction"] == "in")))
    outflow = float(money(sum(r["amount"] for r in rows if r["direction"] == "out")))
    by_category = {}
    for row in rows:
        bucket = by_category.setdefault(row["category"] or "uncategorised", {"in": 0.0, "out": 0.0})
        bucket[row["direction"]] = float(money(bucket[row["direction"]] + row["amount"]))
    return {
        "entries": rows,
        "totals": {
            "inflow": inflow,
            "outflow": outflow,
            "net_liquid_balance": float(money(inflow - outflow)),
        },
        "by_category": by_category,
        "provenance": {"method": "measured", "source": "entries recorded by the user"},
    }


# -------------------------------------------------------------------------- debt


def add_loan(owner, lender, principal, rate, tenure, start_date, facility="",
             status="on_track", balance=None, principal_repaid=0.0, emi=None, scheme_id=""):
    if status not in STATUSES:
        raise ValueError("invalid_status")
    principal = _check_amount(principal, "principal")
    rate = float(rate)
    if not 0 <= rate <= 50:
        raise ValueError("invalid_rate")
    tenure = int(tenure)
    if not 1 <= tenure <= 360:
        raise ValueError("invalid_tenure")
    # The user may enter the EMI the bank actually sanctioned; otherwise the
    # finance engine computes it, so both pages agree.
    computed = float(monthly_emi(principal, rate / 100, tenure))
    row = {
        "id": uuid.uuid4().hex,
        "owner": owner,
        "lender": str(lender)[:120],
        "facility": str(facility)[:120],
        "status": status,
        "principal": principal,
        "rate": rate,
        "tenure": tenure,
        "emi": float(money(emi)) if emi is not None else computed,
        "balance": _check_amount(balance, "balance", allow_zero=True) if balance is not None else principal,
        "principal_repaid": float(money(principal_repaid)),
        "start_date": _check_date(start_date),
        "scheme_id": str(scheme_id)[:60],
        "created": time.time(),
    }
    with db() as c:
        c.execute(
            "INSERT INTO loans VALUES (:id,:owner,:lender,:facility,:status,:principal,"
            ":rate,:tenure,:emi,:balance,:principal_repaid,:start_date,:scheme_id,:created)",
            row,
        )
    row["emi_computed"] = computed
    row["emi_overridden"] = emi is not None and abs(row["emi"] - computed) > 0.01
    return row


def delete_loan(owner, loan_id):
    with db() as c:
        cursor = c.execute("DELETE FROM loans WHERE id=? AND owner=?", (loan_id, owner))
    return cursor.rowcount > 0


def loans(owner):
    with db() as c:
        rows = c.execute(
            "SELECT * FROM loans WHERE owner=? ORDER BY start_date DESC", (owner,)
        ).fetchall()
    return [dict(r) for r in rows]


def debt_summary(owner):
    rows = loans(owner)
    active = [r for r in rows if r["status"] != "closed"]
    return {
        "loans": rows,
        "totals": {
            "outstanding": float(money(sum(r["balance"] for r in active))),
            "principal_repaid": float(money(sum(r["principal_repaid"] for r in rows))),
            "remaining_unpaid": float(money(sum(r["balance"] for r in active))),
            "monthly_emi_obligation": float(money(sum(r["emi"] for r in active))),
            "active_count": len(active),
        },
        "provenance": {"method": "measured", "source": "loans recorded by the user"},
    }
