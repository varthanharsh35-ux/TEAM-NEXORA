"""Task 2.9: Financial statement upload — parse, draft, confirm.

Design rules (from TASKS.md and RULES.md):
  - Accept PDF, CSV, and image uploads.
  - Extracted rows are **drafts** — never written straight into the ledger.
  - Each draft row carries a parse confidence (high / medium / low).
  - A malformed file returns a clear error, not a silent empty result.
  - Only an explicit confirm action promotes drafts into ledger entries.
  - The user may discard any or all draft rows before confirming.

Storage: drafts live in the same SQLite database as the ledger, in their
own table.  This avoids inventing a second database while keeping drafts
cleanly separated from confirmed entries.
"""

import csv
import io
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from finance import money

DB = Path(__file__).resolve().parents[1] / "data" / "ledger.sqlite3"

# Supported MIME prefixes
SUPPORTED_TYPES = {
    "text/csv": "csv",
    "application/csv": "csv",
    "application/vnd.ms-excel": "csv",
    "application/pdf": "pdf",
    "image/png": "image",
    "image/jpeg": "image",
    "image/webp": "image",
    "image/tiff": "image",
}

# Maximum upload sizes in bytes
MAX_CSV_BYTES = 5 * 1024 * 1024       # 5 MB
MAX_PDF_BYTES = 20 * 1024 * 1024      # 20 MB
MAX_IMAGE_BYTES = 10 * 1024 * 1024    # 10 MB


@contextmanager
def _db():
    connection = sqlite3.connect(DB, timeout=15)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS statement_batches ("
                "id TEXT PRIMARY KEY, owner TEXT, filename TEXT,"
                " file_type TEXT, status TEXT, row_count INTEGER,"
                " error_message TEXT, created REAL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS statement_drafts ("
                "id TEXT PRIMARY KEY, batch_id TEXT, owner TEXT,"
                " entry_date TEXT, direction TEXT, amount REAL,"
                " category TEXT, description TEXT,"
                " confidence TEXT, confidence_reason TEXT,"
                " included INTEGER DEFAULT 1, created REAL,"
                " FOREIGN KEY (batch_id) REFERENCES statement_batches(id))"
            )
            yield connection
    finally:
        connection.close()


# ----------------------------------------------------------------- date parsing

# Common date formats found in Indian bank statements and CSV exports.
_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%d-%b-%Y",
    "%d %b %Y",
    "%d-%b-%y",
    "%d/%m/%y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
]


def _parse_date(raw):
    """Try multiple date formats.  Return (iso_date_str, confidence) or None."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(text, fmt)
            if 2000 <= dt.year <= 2100:
                return dt.date().isoformat(), "high"
        except ValueError:
            continue
    # Last resort: try ISO parse
    try:
        dt = date.fromisoformat(text)
        if 2000 <= dt.year <= 2100:
            return dt.isoformat(), "medium"
    except (TypeError, ValueError):
        pass
    return None


# ---------------------------------------------------------------- amount parsing

_AMOUNT_RE = re.compile(
    r"[₹$Rs.INR\s]*"           # optional currency prefix
    r"(-?\s*[\d,]+\.?\d*)",    # digits with optional commas and decimal
    re.IGNORECASE,
)


def _parse_amount(raw):
    """Extract a numeric amount from text.  Returns (float, confidence) or None."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text == "-" or text.lower() in ("nil", "n/a", ""):
        return None
    m = _AMOUNT_RE.search(text)
    if not m:
        return None
    cleaned = m.group(1).replace(",", "").replace(" ", "")
    try:
        value = float(money(cleaned))
    except Exception:
        return None
    if value < 0:
        return abs(value), "medium"
    return value, "high" if "," not in text else "high"


# -------------------------------------------------------------- direction logic

_CREDIT_KEYWORDS = {"credit", "cr", "deposit", "received", "inflow", "in",
                     "salary", "refund", "interest earned"}
_DEBIT_KEYWORDS = {"debit", "dr", "withdrawal", "payment", "outflow", "out",
                    "purchase", "emi", "charge", "fee", "tax"}


def _infer_direction(row_dict, credit_amount=None, debit_amount=None):
    """Infer in/out from column hints and values.

    Returns (direction, confidence).
    """
    # If the CSV has separate debit/credit columns
    if credit_amount is not None and debit_amount is not None:
        if credit_amount > 0 and debit_amount == 0:
            return "in", "high"
        if debit_amount > 0 and credit_amount == 0:
            return "out", "high"
        if credit_amount > 0 and debit_amount > 0:
            return ("in" if credit_amount > debit_amount else "out"), "low"

    if credit_amount is not None and credit_amount > 0:
        return "in", "high"
    if debit_amount is not None and debit_amount > 0:
        return "out", "high"

    # Look at text fields for keywords
    all_text = " ".join(str(v).lower() for v in row_dict.values())
    for kw in _CREDIT_KEYWORDS:
        if kw in all_text:
            return "in", "medium"
    for kw in _DEBIT_KEYWORDS:
        if kw in all_text:
            return "out", "medium"

    return "out", "low"


# ---------------------------------------------------------- category inference

_CATEGORY_KEYWORDS = {
    "sales": ["sale", "sales", "revenue", "sold"],
    "salary": ["salary", "wages", "payroll"],
    "rent": ["rent", "lease"],
    "utilities": ["electricity", "water", "gas", "utility", "bill"],
    "supplies": ["supply", "supplies", "raw material", "material", "feed"],
    "transport": ["transport", "fuel", "petrol", "diesel", "travel"],
    "loan_repayment": ["emi", "loan", "repayment", "instalment"],
    "equipment": ["equipment", "machine", "machinery", "tools"],
    "tax": ["tax", "gst", "tds", "income tax"],
    "insurance": ["insurance", "premium"],
    "maintenance": ["maintenance", "repair"],
    "interest": ["interest"],
    "refund": ["refund", "return"],
}


def _infer_category(row_dict):
    """Best-effort category from description text.  Returns (category, confidence)."""
    all_text = " ".join(str(v).lower() for v in row_dict.values())
    for category, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in all_text:
                return category, "medium"
    return "", "low"


# ------------------------------------------------------------- column matching

# Normalised header names we look for.
_DATE_COLS = {"date", "txn date", "transaction date", "trans date",
              "value date", "posting date", "entry date", "txn_date",
              "transaction_date"}
_AMOUNT_COLS = {"amount", "txn amount", "transaction amount",
                "total", "value", "amt"}
_CREDIT_COLS = {"credit", "credits", "deposit", "cr", "credit amount",
                "credit_amount"}
_DEBIT_COLS = {"debit", "debits", "withdrawal", "dr", "debit amount",
               "debit_amount"}
_DESC_COLS = {"description", "narration", "particulars", "details",
              "remarks", "memo", "note", "narrative", "reference"}


def _norm_header(h):
    return re.sub(r"[^a-z0-9 ]", "", h.lower().strip()).strip()


def _find_col(headers, candidates):
    """Return the first matching column index, or None."""
    for i, h in enumerate(headers):
        if _norm_header(h) in candidates:
            return i
    return None


# --------------------------------------------------------------- CSV parsing

def _parse_csv(content_bytes, filename="upload.csv"):
    """Parse CSV bytes into a list of draft transaction dicts.

    Returns (drafts, error_message).
    """
    try:
        text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content_bytes.decode("latin-1")
        except UnicodeDecodeError:
            return [], "encoding_unsupported"

    # Strip BOM and blank leading lines
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return [], "file_empty_or_no_data_rows"

    try:
        dialect = csv.Sniffer().sniff(lines[0], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel

    reader = csv.reader(lines, dialect)
    rows = list(reader)
    if len(rows) < 2:
        return [], "file_empty_or_no_data_rows"

    headers = rows[0]
    date_col = _find_col(headers, _DATE_COLS)
    amount_col = _find_col(headers, _AMOUNT_COLS)
    credit_col = _find_col(headers, _CREDIT_COLS)
    debit_col = _find_col(headers, _DEBIT_COLS)
    desc_col = _find_col(headers, _DESC_COLS)

    # We need at least a date column and some amount column
    if date_col is None:
        return [], "no_date_column_found"
    if amount_col is None and credit_col is None and debit_col is None:
        return [], "no_amount_column_found"

    drafts = []
    parse_errors = 0
    for row_idx, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue  # skip blank rows

        row_dict = {_norm_header(headers[i]): row[i]
                    for i in range(min(len(headers), len(row)))}

        # Date
        date_val = row[date_col] if date_col < len(row) else ""
        parsed_date = _parse_date(date_val)
        if parsed_date is None:
            parse_errors += 1
            continue
        entry_date, date_confidence = parsed_date

        # Amount(s)
        credit_amount = None
        debit_amount = None
        amount = None

        if credit_col is not None and credit_col < len(row):
            parsed = _parse_amount(row[credit_col])
            credit_amount = parsed[0] if parsed else 0.0

        if debit_col is not None and debit_col < len(row):
            parsed = _parse_amount(row[debit_col])
            debit_amount = parsed[0] if parsed else 0.0

        if amount_col is not None and amount_col < len(row):
            parsed = _parse_amount(row[amount_col])
            if parsed:
                amount, _ = parsed

        # Determine the transaction amount
        if credit_amount and not debit_amount:
            final_amount = credit_amount
        elif debit_amount and not credit_amount:
            final_amount = debit_amount
        elif amount is not None:
            final_amount = amount
        elif credit_amount and debit_amount:
            final_amount = max(credit_amount, debit_amount)
        else:
            parse_errors += 1
            continue

        if final_amount <= 0:
            parse_errors += 1
            continue

        # Direction
        direction, dir_confidence = _infer_direction(
            row_dict,
            credit_amount=credit_amount,
            debit_amount=debit_amount,
        )

        # Category
        category, cat_confidence = _infer_category(row_dict)

        # Description
        description = ""
        if desc_col is not None and desc_col < len(row):
            description = row[desc_col].strip()[:200]

        # Overall confidence is the minimum of component confidences
        confidences = [date_confidence, dir_confidence]
        if cat_confidence != "low":
            confidences.append(cat_confidence)
        confidence_order = {"high": 3, "medium": 2, "low": 1}
        overall = min(confidences, key=lambda c: confidence_order.get(c, 0))

        # Build confidence reason
        reasons = []
        if date_confidence != "high":
            reasons.append("date_format_ambiguous")
        if dir_confidence != "high":
            reasons.append("direction_inferred_from_keywords")
        if dir_confidence == "low":
            reasons.append("direction_unknown")
        confidence_reason = "; ".join(reasons) if reasons else "all_fields_parsed"

        drafts.append({
            "entry_date": entry_date,
            "direction": direction,
            "amount": final_amount,
            "category": category,
            "description": description,
            "confidence": overall,
            "confidence_reason": confidence_reason,
            "source_row": row_idx,
        })

    if not drafts and parse_errors > 0:
        return [], "all_rows_unparseable"
    return drafts, None


# --------------------------------------------------------------- PDF parsing

def _parse_pdf(content_bytes, filename="upload.pdf"):
    """Attempt to parse a PDF bank statement.

    Requires the `pypdf` library.  If absent, returns a clear error rather
    than a silent failure (rule 6).
    """
    try:
        import pypdf
    except ImportError:
        return [], "pdf_parser_unavailable"

    try:
        reader = pypdf.PdfReader(io.BytesIO(content_bytes))
    except Exception:
        return [], "pdf_corrupt_or_unreadable"

    if len(reader.pages) == 0:
        return [], "pdf_empty"

    # Extract all text and try to parse it as CSV-like lines
    all_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            all_text.append(text)

    if not all_text:
        return [], "pdf_no_extractable_text"

    # Try treating the extracted text as CSV
    combined = "\n".join(all_text)
    return _parse_csv(combined.encode("utf-8"), filename)


# ------------------------------------------------------------- image parsing

def _parse_image(content_bytes, filename="upload.jpg"):
    """Placeholder for OCR-based parsing.

    OCR is not configured.  Returns a clear error per rule 6: no silent
    failure, no pretending the image is empty.
    """
    return [], "image_ocr_not_configured"


# ------------------------------------------------------------- main interface

PARSERS = {
    "csv": _parse_csv,
    "pdf": _parse_pdf,
    "image": _parse_image,
}


def parse_statement(content_bytes, filename, content_type=None):
    """Detect file type and parse.

    Returns (file_type, drafts, error_message).
    """
    if not content_bytes:
        return None, [], "file_empty"

    # Determine parser
    file_type = None
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        file_type = SUPPORTED_TYPES.get(ct)

    # Fallback to extension
    if file_type is None and filename:
        ext = Path(filename).suffix.lower()
        if ext == ".csv":
            file_type = "csv"
        elif ext == ".pdf":
            file_type = "pdf"
        elif ext in (".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"):
            file_type = "image"

    if file_type is None:
        return None, [], "unsupported_file_type"

    # Size checks
    size = len(content_bytes)
    limits = {"csv": MAX_CSV_BYTES, "pdf": MAX_PDF_BYTES, "image": MAX_IMAGE_BYTES}
    if size > limits.get(file_type, MAX_CSV_BYTES):
        return file_type, [], "file_too_large"

    parser = PARSERS.get(file_type)
    if parser is None:
        return file_type, [], "unsupported_file_type"

    drafts, error = parser(content_bytes, filename)
    return file_type, drafts, error


# ------------------------------------------------------------ batch storage

def create_batch(owner, filename, content_bytes, content_type=None):
    """Parse an uploaded file and store the results as a draft batch.

    Returns the batch record with nested draft rows.  Never touches the
    ledger — that only happens on explicit confirm.
    """
    file_type, drafts, error = parse_statement(
        content_bytes, filename, content_type
    )

    batch_id = uuid.uuid4().hex
    now = time.time()

    batch = {
        "id": batch_id,
        "owner": owner,
        "filename": str(filename)[:200] if filename else "unknown",
        "file_type": file_type or "unknown",
        "status": "parsed" if drafts else "error",
        "row_count": len(drafts),
        "error_message": error,
        "created": now,
    }

    with _db() as c:
        c.execute(
            "INSERT INTO statement_batches VALUES "
            "(:id, :owner, :filename, :file_type, :status,"
            " :row_count, :error_message, :created)",
            batch,
        )

        for draft in drafts:
            draft_row = {
                "id": uuid.uuid4().hex,
                "batch_id": batch_id,
                "owner": owner,
                "entry_date": draft["entry_date"],
                "direction": draft["direction"],
                "amount": draft["amount"],
                "category": draft["category"],
                "description": draft["description"],
                "confidence": draft["confidence"],
                "confidence_reason": draft["confidence_reason"],
                "included": 1,
                "created": now,
            }
            c.execute(
                "INSERT INTO statement_drafts VALUES "
                "(:id, :batch_id, :owner, :entry_date, :direction,"
                " :amount, :category, :description, :confidence,"
                " :confidence_reason, :included, :created)",
                draft_row,
            )

    return get_batch(owner, batch_id)


def get_batch(owner, batch_id):
    """Retrieve a batch with all its draft rows."""
    with _db() as c:
        batch_row = c.execute(
            "SELECT * FROM statement_batches WHERE id=? AND owner=?",
            (batch_id, owner),
        ).fetchone()
        if batch_row is None:
            return None

        draft_rows = c.execute(
            "SELECT * FROM statement_drafts WHERE batch_id=? AND owner=?"
            " ORDER BY entry_date ASC, created ASC",
            (batch_id, owner),
        ).fetchall()

    batch = dict(batch_row)
    batch["drafts"] = [dict(r) for r in draft_rows]
    return batch


def list_batches(owner):
    """List all batches for a user, without draft rows."""
    with _db() as c:
        rows = c.execute(
            "SELECT * FROM statement_batches WHERE owner=?"
            " ORDER BY created DESC",
            (owner,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_draft(owner, draft_id, included=None, direction=None,
                 category=None, amount=None, entry_date=None):
    """Let the user correct a draft row before confirming.

    Only unconfirmed batches may be edited.
    """
    with _db() as c:
        row = c.execute(
            "SELECT d.*, b.status AS batch_status"
            " FROM statement_drafts d"
            " JOIN statement_batches b ON d.batch_id = b.id"
            " WHERE d.id=? AND d.owner=?",
            (draft_id, owner),
        ).fetchone()
        if row is None:
            return None
        if row["batch_status"] == "confirmed":
            raise ValueError("batch_already_confirmed")

        updates = []
        params = []
        if included is not None:
            updates.append("included=?")
            params.append(1 if included else 0)
        if direction is not None:
            if direction not in ("in", "out"):
                raise ValueError("invalid_direction")
            updates.append("direction=?")
            params.append(direction)
        if category is not None:
            updates.append("category=?")
            params.append(str(category)[:60])
        if amount is not None:
            try:
                amount = float(money(amount))
            except Exception:
                raise ValueError("invalid_amount")
            if amount <= 0:
                raise ValueError("invalid_amount")
            updates.append("amount=?")
            params.append(amount)
        if entry_date is not None:
            try:
                parsed = date.fromisoformat(entry_date)
                if not 2000 <= parsed.year <= 2100:
                    raise ValueError()
            except (TypeError, ValueError):
                raise ValueError("invalid_date")
            updates.append("entry_date=?")
            params.append(parsed.isoformat())

        if not updates:
            return dict(row)

        params.extend([draft_id, owner])
        c.execute(
            f"UPDATE statement_drafts SET {', '.join(updates)}"
            f" WHERE id=? AND owner=?",
            params,
        )

    # Return the fresh row
    with _db() as c:
        updated = c.execute(
            "SELECT * FROM statement_drafts WHERE id=? AND owner=?",
            (draft_id, owner),
        ).fetchone()
    return dict(updated) if updated else None


def discard_batch(owner, batch_id):
    """Discard an entire batch.  Marks it discarded, does not delete (rule 1)."""
    with _db() as c:
        row = c.execute(
            "SELECT * FROM statement_batches WHERE id=? AND owner=?",
            (batch_id, owner),
        ).fetchone()
        if row is None:
            return False
        if row["status"] == "confirmed":
            raise ValueError("batch_already_confirmed")
        c.execute(
            "UPDATE statement_batches SET status='discarded' WHERE id=? AND owner=?",
            (batch_id, owner),
        )
        c.execute(
            "UPDATE statement_drafts SET included=0 WHERE batch_id=? AND owner=?",
            (batch_id, owner),
        )
    return True


def confirm_batch(owner, batch_id):
    """Promote included drafts into real ledger entries.

    This is the ONLY path from draft to ledger.  Returns a summary of
    what was committed.
    """
    import ledger

    batch = get_batch(owner, batch_id)
    if batch is None:
        return None
    if batch["status"] == "confirmed":
        raise ValueError("batch_already_confirmed")
    if batch["status"] == "discarded":
        raise ValueError("batch_already_discarded")

    included = [d for d in batch["drafts"] if d["included"]]
    if not included:
        raise ValueError("no_drafts_selected")

    committed = []
    for draft in included:
        entry = ledger.add_entry(
            owner=owner,
            entry_date=draft["entry_date"],
            direction=draft["direction"],
            amount=draft["amount"],
            category=draft["category"],
            note=f"from statement: {batch['filename']}",
        )
        committed.append(entry["id"])

    with _db() as c:
        c.execute(
            "UPDATE statement_batches SET status='confirmed' WHERE id=? AND owner=?",
            (batch_id, owner),
        )

    return {
        "batch_id": batch_id,
        "status": "confirmed",
        "committed_count": len(committed),
        "committed_entry_ids": committed,
        "skipped_count": len(batch["drafts"]) - len(included),
    }
