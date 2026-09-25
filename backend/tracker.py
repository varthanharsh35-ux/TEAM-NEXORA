"""Cash flow tracker and loan servicing engine backed by SQLite."""

import datetime
import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

from storage import database_path
DB_PATH = database_path('tracker.sqlite3')


def _get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                kind TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_user ON entries (user_id, date)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS loan_plans (
                user_id TEXT PRIMARY KEY,
                scheme_id TEXT NOT NULL,
                sanctioned REAL NOT NULL,
                disbursement_date TEXT NOT NULL,
                schedule TEXT NOT NULL
            )
        """)
    return conn


def _validate_date(d_str: str):
    if not isinstance(d_str, str):
        raise ValueError("invalid_date")
    try:
        datetime.date.fromisoformat(d_str)
    except Exception:
        raise ValueError("invalid_date")


def add_entry(user_id: str, date: str, kind: str, category: str, amount: float, note: str = "") -> dict:
    """Record a cash inflow or outflow."""
    if not user_id or not isinstance(user_id, str):
        raise ValueError("invalid_user_id")
    _validate_date(date)
    k = (kind or "").strip().lower()
    if k not in ("income", "expense"):
        raise ValueError("invalid_kind")
    if not category or not isinstance(category, str):
        raise ValueError("invalid_category")
    try:
        amt = float(amount)
        if amt <= 0 or not (amt == amt):  # NaN check
            raise ValueError("invalid_amount")
    except (TypeError, ValueError):
        raise ValueError("invalid_amount")

    entry_id = str(uuid.uuid4())
    clean_note = (note or "").strip()

    with closing(_get_connection()) as conn:
        with conn:
            conn.execute(
                "INSERT INTO entries (id, user_id, date, kind, category, amount, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entry_id, user_id, date, k, category.strip().lower(), amt, clean_note)
            )

    return {
        "id": entry_id,
        "user_id": user_id,
        "date": date,
        "kind": k,
        "category": category.strip().lower(),
        "amount": round(amt, 2),
        "note": clean_note
    }


def delete_entry(user_id: str, entry_id: str) -> bool:
    """Delete an entry by ID for a user."""
    if not user_id or not entry_id:
        return False
    with closing(_get_connection()) as conn:
        with conn:
            cur = conn.execute("DELETE FROM entries WHERE id = ? AND user_id = ?", (entry_id, user_id))
            return cur.rowcount > 0


def save_loan_plan(user_id: str, scheme_id: str, sanctioned: float, schedule: list, disbursement_date: str) -> dict:
    """Persist an sanctioned loan schedule for cash flow forecasting."""
    if not user_id or not scheme_id:
        raise ValueError("invalid_loan_plan")
    _validate_date(disbursement_date)
    sanct = float(sanctioned)
    if sanct <= 0:
        raise ValueError("invalid_sanctioned_amount")

    sched_json = json.dumps(schedule or [])
    with closing(_get_connection()) as conn:
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO loan_plans (user_id, scheme_id, sanctioned, disbursement_date, schedule) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, scheme_id, sanct, disbursement_date, sched_json)
            )

    return {
        "user_id": user_id,
        "scheme_id": scheme_id,
        "sanctioned": round(sanct, 2),
        "disbursement_date": disbursement_date,
        "schedule": schedule or []
    }


def get_loan_status(user_id: str) -> dict | None:
    """Return loan repayment status tracking actual emi payments against plan."""
    if not user_id:
        return None
    with closing(_get_connection()) as conn:
        row = conn.execute(
            "SELECT scheme_id, sanctioned, disbursement_date, schedule FROM loan_plans WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if not row:
            return None

        scheme_id, sanctioned, disb_date, sched_json = row
        schedule = json.loads(sched_json)

        # Sum entries where category == "emi"
        cur = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM entries WHERE user_id = ? AND category = 'emi'",
            (user_id,)
        )
        paid_to_date = float(cur.fetchone()[0])

    # Determine next due and moratorium state from schedule
    cumulative = 0.0
    next_due = None
    next_amount = None
    in_moratorium = False

    for item in schedule:
        pay = float(item.get("payment", 0))
        cumulative += pay
        if cumulative > paid_to_date + 0.01:
            next_due = item.get("due_date")
            next_amount = pay
            in_moratorium = bool(item.get("moratorium", False))
            break

    # If first installment still pending and pay == 0, check first schedule item
    if next_due is None and schedule:
        first = schedule[0]
        if paid_to_date < 0.01:
            next_due = first.get("due_date")
            next_amount = float(first.get("payment", 0))
            in_moratorium = bool(first.get("moratorium", False))

    return {
        "scheme_id": scheme_id,
        "sanctioned": round(float(sanctioned), 2),
        "paid_to_date": round(paid_to_date, 2),
        "next_due": next_due,
        "next_amount": round(next_amount, 2) if next_amount is not None else None,
        "in_moratorium": in_moratorium
    }


def summary(user_id: str, from_date: str = None, to_date: str = None) -> dict:
    """Compute fresh inflow, outflow, net liquid balance, loan status, and actual vs forecast."""
    if not user_id:
        raise ValueError("invalid_user_id")

    query = "SELECT id, user_id, date, kind, category, amount, note FROM entries WHERE user_id = ?"
    params = [user_id]
    if from_date:
        _validate_date(from_date)
        query += " AND date >= ?"
        params.append(from_date)
    if to_date:
        _validate_date(to_date)
        query += " AND date <= ?"
        params.append(to_date)
    query += " ORDER BY date ASC, id ASC"

    entries = []
    tot_income = 0.0
    tot_expense = 0.0
    monthly_actuals = {}

    with closing(_get_connection()) as conn:
        cur = conn.execute(query, params)
        for r in cur.fetchall():
            amt = float(r[5])
            ent = {
                "id": r[0],
                "user_id": r[1],
                "date": r[2],
                "kind": r[3],
                "category": r[4],
                "amount": round(amt, 2),
                "note": r[6]
            }
            entries.append(ent)
            month_key = r[2][:7]  # YYYY-MM
            if r[3] == "income":
                tot_income += amt
                monthly_actuals[month_key] = monthly_actuals.get(month_key, 0.0) + amt
            else:
                tot_expense += amt
                monthly_actuals[month_key] = monthly_actuals.get(month_key, 0.0) - amt

        # Forecast from loan plan schedule
        row = conn.execute("SELECT schedule FROM loan_plans WHERE user_id = ?", (user_id,)).fetchone()
        forecast_by_month = {}
        if row:
            sched = json.loads(row[0])
            for s in sched:
                due = s.get("due_date", "")
                if len(due) >= 7:
                    m = due[:7]
                    forecast_by_month[m] = forecast_by_month.get(m, 0.0) + float(s.get("payment", 0))

    # Build actual vs forecast months (never blended)
    all_months = sorted(set(monthly_actuals.keys()) | set(forecast_by_month.keys()))
    actual_vs_forecast = [
        {
            "month": m,
            "forecast": round(forecast_by_month[m], 2) if m in forecast_by_month else None,
            "actual": round(monthly_actuals.get(m, 0.0), 2)
        }
        for m in all_months
    ]

    return {
        "entries": entries,
        "totals": {
            "income": round(tot_income, 2),
            "expense": round(tot_expense, 2),
            "net": round(tot_income - tot_expense, 2)
        },
        "loan_status": get_loan_status(user_id),
        "actual_vs_forecast": actual_vs_forecast
    }


if __name__ == "__main__":
    test_user = "test_user_" + str(uuid.uuid4())[:8]

    # 1. Add income entry
    e1 = add_entry(test_user, "2026-01-15", "income", "sales", 5000.0, "Morning market sales")
    assert e1["kind"] == "income"
    assert e1["amount"] == 5000.0
    assert e1["user_id"] == test_user

    # 2. Add expense entry
    e2 = add_entry(test_user, "2026-01-20", "expense", "raw_material", 1500.0, "Seeds and feed")
    assert e2["kind"] == "expense"
    assert e2["amount"] == 1500.0

    # 3. Add EMI payment entry
    e3 = add_entry(test_user, "2026-03-25", "expense", "emi", 12000.0, "Quarterly EMI")
    assert e3["category"] == "emi"

    # 4. Summary computes fresh totals
    s1 = summary(test_user)
    assert s1["totals"]["income"] == 5000.0
    assert s1["totals"]["expense"] == 13500.0
    assert s1["totals"]["net"] == -8500.0
    assert len(s1["entries"]) == 3

    # 5. Delete entry updates totals fresh
    deleted = delete_entry(test_user, e2["id"])
    assert deleted is True
    s2 = summary(test_user)
    assert s2["totals"]["expense"] == 12000.0
    assert s2["totals"]["net"] == -7000.0
    assert len(s2["entries"]) == 2

    # 6. Deleting non-existent entry returns False
    assert delete_entry(test_user, "non_existent_id") is False

    # 7. Invalid inputs raise ValueError
    try:
        add_entry(test_user, "bad-date", "income", "sales", 100)
        assert False, "Should fail on bad date"
    except ValueError:
        pass

    try:
        add_entry(test_user, "2026-01-01", "invalid_kind", "sales", 100)
        assert False, "Should fail on invalid kind"
    except ValueError:
        pass

    try:
        add_entry(test_user, "2026-01-01", "income", "sales", -50)
        assert False, "Should fail on negative amount"
    except ValueError:
        pass

    # 8. Loan plan persistence
    mock_schedule = [
        {"month": 3, "due_date": "2026-03-25", "payment": 12000.0, "moratorium": False},
        {"month": 6, "due_date": "2026-06-25", "payment": 12000.0, "moratorium": False}
    ]
    lp = save_loan_plan(test_user, "nsfdc.micro", 100000.0, mock_schedule, "2026-01-01")
    assert lp["scheme_id"] == "nsfdc.micro"
    assert lp["sanctioned"] == 100000.0

    # 9. Loan status reflects paid EMI
    status = get_loan_status(test_user)
    assert status is not None
    assert status["scheme_id"] == "nsfdc.micro"
    assert status["sanctioned"] == 100000.0
    assert status["paid_to_date"] == 12000.0
    assert status["next_due"] == "2026-06-25"
    assert status["next_amount"] == 12000.0
    assert status["in_moratorium"] is False

    # 10. Actual vs forecast months separated and unblended
    s3 = summary(test_user)
    avf = {x["month"]: x for x in s3["actual_vs_forecast"]}
    assert "2026-01" in avf
    assert avf["2026-01"]["actual"] == 5000.0
    assert avf["2026-01"]["forecast"] is None
    assert "2026-06" in avf
    assert avf["2026-06"]["forecast"] == 12000.0

    # 11. Date range filtering in summary
    s_filtered = summary(test_user, from_date="2026-02-01", to_date="2026-03-31")
    assert len(s_filtered["entries"]) == 1
    assert s_filtered["entries"][0]["category"] == "emi"

    # 12. Cleanup user data
    for ent in summary(test_user)["entries"]:
        delete_entry(test_user, ent["id"])
    assert len(summary(test_user)["entries"]) == 0

    print("All 12+ tracker tests passed successfully!")
