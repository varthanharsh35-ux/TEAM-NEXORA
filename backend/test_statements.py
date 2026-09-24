"""Task 2.9: tests for financial statement upload."""
import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import statements
import ledger


class StatementTestCase(unittest.TestCase):
    """Base with a temporary database for both statements and ledger."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        db_path = Path(self.temp.name) / "ledger.sqlite3"
        self.patches = [
            patch.object(statements, "DB", db_path),
            patch.object(ledger, "DB", db_path),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()


def _make_csv(rows, headers=None):
    """Build CSV bytes from a list of dicts or list of lists."""
    buf = io.StringIO()
    if headers is None:
        headers = list(rows[0].keys())
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


# --------------------------------------------------------- CSV parsing tests


class CSVParsing(StatementTestCase):

    def test_basic_csv_with_debit_credit_columns(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "Feed purchase",
             "Debit": "2400", "Credit": ""},
            {"Date": "2026-10-02", "Description": "Sales revenue",
             "Debit": "", "Credit": "5000"},
        ])
        batch = statements.create_batch("u1", "test.csv", data, "text/csv")
        self.assertEqual(batch["status"], "parsed")
        self.assertEqual(batch["row_count"], 2)
        self.assertEqual(len(batch["drafts"]), 2)

        # First row is a debit = outflow
        d0 = batch["drafts"][0]
        self.assertEqual(d0["direction"], "out")
        self.assertEqual(d0["amount"], 2400)
        self.assertIn(d0["confidence"], ("high", "medium"))

        # Second row is a credit = inflow
        d1 = batch["drafts"][1]
        self.assertEqual(d1["direction"], "in")
        self.assertEqual(d1["amount"], 5000)

    def test_single_amount_column_with_description_keywords(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Narration": "EMI payment SBI",
             "Amount": "3500"},
            {"Date": "2026-10-02", "Narration": "Salary received",
             "Amount": "25000"},
        ])
        batch = statements.create_batch("u1", "test.csv", data, "text/csv")
        self.assertEqual(batch["row_count"], 2)
        d0 = batch["drafts"][0]
        self.assertEqual(d0["direction"], "out")
        self.assertEqual(d0["category"], "loan_repayment")

        d1 = batch["drafts"][1]
        self.assertEqual(d1["direction"], "in")
        self.assertEqual(d1["category"], "salary")

    def test_indian_date_format_dd_mm_yyyy(self):
        data = _make_csv([
            {"Date": "15/03/2026", "Description": "test", "Amount": "100"},
        ])
        batch = statements.create_batch("u1", "test.csv", data)
        self.assertEqual(batch["drafts"][0]["entry_date"], "2026-03-15")

    def test_amounts_with_commas_and_currency_symbols(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Details": "deposit",
             "Credit": "₹1,25,000.50", "Debit": ""},
        ])
        batch = statements.create_batch("u1", "test.csv", data)
        self.assertEqual(batch["drafts"][0]["amount"], 125000.50)

    def test_empty_csv_fails_with_clear_message(self):
        batch = statements.create_batch("u1", "empty.csv", b"", "text/csv")
        self.assertEqual(batch["status"], "error")
        self.assertIsNotNone(batch["error_message"])

    def test_csv_with_only_headers_fails(self):
        data = b"Date,Amount,Description\n"
        batch = statements.create_batch("u1", "headers_only.csv", data, "text/csv")
        self.assertEqual(batch["status"], "error")

    def test_csv_without_date_column_fails(self):
        data = _make_csv([
            {"Name": "test", "Value": "100"},
        ])
        batch = statements.create_batch("u1", "bad.csv", data, "text/csv")
        self.assertEqual(batch["status"], "error")
        self.assertEqual(batch["error_message"], "no_date_column_found")

    def test_csv_without_amount_column_fails(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Name": "test"},
        ])
        batch = statements.create_batch("u1", "bad.csv", data, "text/csv")
        self.assertEqual(batch["status"], "error")
        self.assertEqual(batch["error_message"], "no_amount_column_found")

    def test_malformed_rows_are_skipped_not_fatal(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "good", "Amount": "100"},
            {"Date": "not-a-date", "Description": "bad", "Amount": "200"},
            {"Date": "2026-10-03", "Description": "good", "Amount": "300"},
        ])
        batch = statements.create_batch("u1", "mixed.csv", data)
        self.assertEqual(batch["row_count"], 2)
        self.assertEqual(batch["status"], "parsed")

    def test_all_rows_unparseable_returns_error(self):
        data = _make_csv([
            {"Date": "nope", "Description": "bad", "Amount": "abc"},
            {"Date": "also-nope", "Description": "bad", "Amount": "xyz"},
        ])
        batch = statements.create_batch("u1", "bad.csv", data)
        self.assertEqual(batch["status"], "error")

    def test_confidence_shown_per_row(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "Feed purchase",
             "Debit": "2400", "Credit": ""},
            {"Date": "2026-10-02", "Description": "unknown thing",
             "Debit": "", "Credit": "500"},
        ])
        batch = statements.create_batch("u1", "test.csv", data)
        self.assertEqual(batch["row_count"], 2)
        for draft in batch["drafts"]:
            self.assertIn(draft["confidence"], ("high", "medium", "low"))
            self.assertIsNotNone(draft["confidence_reason"])
            self.assertIsInstance(draft["confidence_reason"], str)


# --------------------------------------------------- draft workflow tests


class DraftWorkflow(StatementTestCase):

    def _upload(self, owner="u1"):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "Feed",
             "Debit": "2400", "Credit": ""},
            {"Date": "2026-10-02", "Description": "Sales",
             "Debit": "", "Credit": "5000"},
            {"Date": "2026-10-03", "Description": "Rent",
             "Debit": "8000", "Credit": ""},
        ])
        return statements.create_batch(owner, "test.csv", data)

    def test_drafts_are_not_in_the_ledger(self):
        """The core rule: parsed rows are drafts, not ledger entries."""
        self._upload()
        summary = ledger.cash_summary("u1")
        self.assertEqual(summary["totals"]["inflow"], 0)
        self.assertEqual(summary["totals"]["outflow"], 0)
        self.assertEqual(len(summary["entries"]), 0)

    def test_confirm_promotes_drafts_to_ledger(self):
        batch = self._upload()
        result = statements.confirm_batch("u1", batch["id"])
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["committed_count"], 3)

        summary = ledger.cash_summary("u1")
        self.assertEqual(summary["totals"]["inflow"], 5000)
        self.assertEqual(summary["totals"]["outflow"], 10400)

    def test_excluded_drafts_are_not_committed(self):
        batch = self._upload()
        # Exclude the rent row
        rent_draft = batch["drafts"][2]
        statements.update_draft("u1", rent_draft["id"], included=False)

        result = statements.confirm_batch("u1", batch["id"])
        self.assertEqual(result["committed_count"], 2)
        self.assertEqual(result["skipped_count"], 1)

        summary = ledger.cash_summary("u1")
        self.assertEqual(summary["totals"]["outflow"], 2400)

    def test_cannot_confirm_twice(self):
        batch = self._upload()
        statements.confirm_batch("u1", batch["id"])
        with self.assertRaises(ValueError) as ctx:
            statements.confirm_batch("u1", batch["id"])
        self.assertIn("already_confirmed", str(ctx.exception))

    def test_discard_prevents_confirm(self):
        batch = self._upload()
        self.assertTrue(statements.discard_batch("u1", batch["id"]))
        with self.assertRaises(ValueError) as ctx:
            statements.confirm_batch("u1", batch["id"])
        self.assertIn("discarded", str(ctx.exception))

    def test_cannot_discard_confirmed_batch(self):
        batch = self._upload()
        statements.confirm_batch("u1", batch["id"])
        with self.assertRaises(ValueError):
            statements.discard_batch("u1", batch["id"])

    def test_user_can_correct_draft_before_confirming(self):
        batch = self._upload()
        draft = batch["drafts"][0]
        updated = statements.update_draft(
            "u1", draft["id"],
            direction="in", category="refund", amount=2500,
        )
        self.assertEqual(updated["direction"], "in")
        self.assertEqual(updated["category"], "refund")
        self.assertEqual(updated["amount"], 2500)

    def test_cannot_edit_draft_after_confirm(self):
        batch = self._upload()
        statements.confirm_batch("u1", batch["id"])
        with self.assertRaises(ValueError):
            statements.update_draft(
                "u1", batch["drafts"][0]["id"], direction="in",
            )

    def test_draft_update_validates_direction(self):
        batch = self._upload()
        with self.assertRaises(ValueError):
            statements.update_draft(
                "u1", batch["drafts"][0]["id"], direction="sideways",
            )

    def test_draft_update_validates_amount(self):
        batch = self._upload()
        with self.assertRaises(ValueError):
            statements.update_draft(
                "u1", batch["drafts"][0]["id"], amount=-100,
            )

    def test_draft_update_validates_date(self):
        batch = self._upload()
        with self.assertRaises(ValueError):
            statements.update_draft(
                "u1", batch["drafts"][0]["id"], entry_date="nope",
            )

    def test_no_drafts_selected_raises_error(self):
        batch = self._upload()
        for d in batch["drafts"]:
            statements.update_draft("u1", d["id"], included=False)
        with self.assertRaises(ValueError) as ctx:
            statements.confirm_batch("u1", batch["id"])
        self.assertIn("no_drafts_selected", str(ctx.exception))


# --------------------------------------------------- isolation and scoping


class Isolation(StatementTestCase):

    def test_batches_are_scoped_per_user(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "test", "Amount": "100",
             "Debit": "100", "Credit": ""},
        ])
        statements.create_batch("u1", "test.csv", data)
        self.assertEqual(len(statements.list_batches("u1")), 1)
        self.assertEqual(len(statements.list_batches("u2")), 0)

    def test_user_cannot_confirm_anothers_batch(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "test",
             "Debit": "100", "Credit": ""},
        ])
        batch = statements.create_batch("u1", "test.csv", data)
        result = statements.confirm_batch("u2", batch["id"])
        self.assertIsNone(result)

    def test_user_cannot_edit_anothers_draft(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "test",
             "Debit": "100", "Credit": ""},
        ])
        batch = statements.create_batch("u1", "test.csv", data)
        result = statements.update_draft(
            "u2", batch["drafts"][0]["id"], direction="in",
        )
        self.assertIsNone(result)


# --------------------------------------------------- file type handling


class FileTypes(StatementTestCase):

    def test_unsupported_file_type_fails(self):
        batch = statements.create_batch(
            "u1", "data.xlsx", b"some content",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(batch["status"], "error")
        self.assertEqual(batch["error_message"], "unsupported_file_type")

    def test_image_returns_ocr_not_configured(self):
        batch = statements.create_batch(
            "u1", "statement.png", b"\x89PNG\r\n", "image/png",
        )
        self.assertEqual(batch["status"], "error")
        self.assertEqual(batch["error_message"], "image_ocr_not_configured")

    def test_pdf_without_library_returns_clear_error(self):
        # pypdf is not installed in this environment
        batch = statements.create_batch(
            "u1", "statement.pdf", b"%PDF-1.4 fake", "application/pdf",
        )
        self.assertEqual(batch["status"], "error")
        self.assertIn(batch["error_message"],
                       ("pdf_parser_unavailable", "pdf_corrupt_or_unreadable"))

    def test_csv_detected_by_extension(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "test",
             "Debit": "100", "Credit": ""},
        ])
        batch = statements.create_batch("u1", "data.csv", data)
        self.assertEqual(batch["file_type"], "csv")
        self.assertEqual(batch["status"], "parsed")

    def test_file_too_large_is_rejected(self):
        original = statements.MAX_CSV_BYTES
        try:
            statements.MAX_CSV_BYTES = 10
            data = _make_csv([
                {"Date": "2026-10-01", "Description": "test",
                 "Debit": "100", "Credit": ""},
            ])
            batch = statements.create_batch("u1", "big.csv", data)
            self.assertEqual(batch["status"], "error")
            self.assertEqual(batch["error_message"], "file_too_large")
        finally:
            statements.MAX_CSV_BYTES = original


# --------------------------------------------------- batch listing


class BatchListing(StatementTestCase):

    def test_list_batches_returns_all(self):
        data = _make_csv([
            {"Date": "2026-10-01", "Description": "test",
             "Debit": "100", "Credit": ""},
        ])
        statements.create_batch("u1", "a.csv", data)
        statements.create_batch("u1", "b.csv", data)
        batches = statements.list_batches("u1")
        self.assertEqual(len(batches), 2)

    def test_get_batch_returns_none_for_missing(self):
        self.assertIsNone(statements.get_batch("u1", "nonexistent"))


# ------------------------------------------------------ semicolon-delimited


class AlternateDelimiters(StatementTestCase):

    def test_semicolon_separated_csv(self):
        content = (
            "Date;Description;Debit;Credit\n"
            "01/10/2026;Feed purchase;2400;\n"
            "02/10/2026;Sales revenue;;5000\n"
        ).encode("utf-8")
        batch = statements.create_batch("u1", "test.csv", content)
        self.assertEqual(batch["status"], "parsed")
        self.assertEqual(batch["row_count"], 2)


if __name__ == "__main__":
    unittest.main()
