"""Task 2.8: cash flow and debt ledgers."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ledger
from finance import monthly_emi


class LedgerCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch = patch.object(ledger, 'DB', Path(self.temp.name) / 'ledger.sqlite3')
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(self.temp.cleanup)


class CashFlow(LedgerCase):
    def test_totals_and_net_balance(self):
        ledger.add_entry('u1', '2026-10-01', 'in', 2400, 'sales')
        ledger.add_entry('u1', '2026-10-02', 'in', 1600, 'sales')
        ledger.add_entry('u1', '2026-10-03', 'out', 900, 'feed')
        totals = ledger.cash_summary('u1')['totals']
        self.assertEqual(totals['inflow'], 4000)
        self.assertEqual(totals['outflow'], 900)
        self.assertEqual(totals['net_liquid_balance'], 3100)

    def test_totals_recompute_after_delete(self):
        row = ledger.add_entry('u1', '2026-10-01', 'in', 2400, 'sales')
        ledger.add_entry('u1', '2026-10-02', 'out', 400, 'feed')
        self.assertTrue(ledger.delete_entry('u1', row['id']))
        totals = ledger.cash_summary('u1')['totals']
        self.assertEqual(totals['inflow'], 0)
        self.assertEqual(totals['net_liquid_balance'], -400)

    def test_one_user_cannot_delete_anothers_entry(self):
        row = ledger.add_entry('u1', '2026-10-01', 'in', 100, 'sales')
        self.assertFalse(ledger.delete_entry('u2', row['id']))
        self.assertEqual(len(ledger.entries('u1')), 1)

    def test_entries_are_scoped_per_user(self):
        ledger.add_entry('u1', '2026-10-01', 'in', 100)
        ledger.add_entry('u2', '2026-10-01', 'in', 999)
        self.assertEqual(ledger.cash_summary('u1')['totals']['inflow'], 100)

    def test_date_range_filter(self):
        ledger.add_entry('u1', '2026-10-01', 'in', 100)
        ledger.add_entry('u1', '2026-11-05', 'in', 200)
        summary = ledger.cash_summary('u1', start='2026-11-01', end='2026-11-30')
        self.assertEqual(summary['totals']['inflow'], 200)

    def test_bad_input_is_rejected(self):
        for bad in [
            lambda: ledger.add_entry('u1', 'not-a-date', 'in', 100),
            lambda: ledger.add_entry('u1', '2026-10-01', 'sideways', 100),
            lambda: ledger.add_entry('u1', '2026-10-01', 'in', -5),
            lambda: ledger.add_entry('u1', '2026-10-01', 'in', 0),
            lambda: ledger.add_entry('u1', '1799-01-01', 'in', 100),
        ]:
            with self.assertRaises(ValueError):
                bad()

    def test_recorded_data_is_labelled_measured(self):
        ledger.add_entry('u1', '2026-10-01', 'in', 100)
        self.assertEqual(ledger.cash_summary('u1')['provenance']['method'], 'measured')


class Debt(LedgerCase):
    def loan(self, **kw):
        base = dict(owner='u1', lender='SBI', principal=100000, rate=8, tenure=36,
                    start_date='2026-10-01', facility='MUDRA Kishore')
        base.update(kw)
        return ledger.add_loan(**base)

    def test_emi_comes_from_the_finance_engine(self):
        """The debt page and the funding plan must never disagree."""
        row = self.loan()
        self.assertEqual(row['emi'], float(monthly_emi(100000, 0.08, 36)))
        self.assertFalse(row['emi_overridden'])

    def test_sanctioned_emi_can_override_the_estimate_and_is_flagged(self):
        row = self.loan(emi=3200)
        self.assertEqual(row['emi'], 3200)
        self.assertTrue(row['emi_overridden'])
        self.assertAlmostEqual(row['emi_computed'], float(monthly_emi(100000, 0.08, 36)), places=2)

    def test_portfolio_totals(self):
        self.loan(principal=100000, balance=90000, principal_repaid=10000)
        self.loan(lender='BoB', principal=50000, balance=50000, tenure=24)
        totals = ledger.debt_summary('u1')['totals']
        self.assertEqual(totals['outstanding'], 140000)
        self.assertEqual(totals['principal_repaid'], 10000)
        self.assertEqual(totals['active_count'], 2)
        expected = float(monthly_emi(100000, 0.08, 36)) + float(monthly_emi(50000, 0.08, 24))
        self.assertAlmostEqual(totals['monthly_emi_obligation'], expected, places=2)

    def test_closed_loans_leave_the_obligation(self):
        self.loan(principal=100000, balance=0, status='closed', principal_repaid=100000)
        totals = ledger.debt_summary('u1')['totals']
        self.assertEqual(totals['outstanding'], 0)
        self.assertEqual(totals['monthly_emi_obligation'], 0)
        self.assertEqual(totals['principal_repaid'], 100000)
        self.assertEqual(len(ledger.debt_summary('u1')['loans']), 1, 'closed loans stay visible')

    def test_zero_interest_loan_is_supported(self):
        row = self.loan(rate=0, principal=120000, tenure=12)
        self.assertEqual(row['emi'], 10000)

    def test_bad_loan_input_is_rejected(self):
        for bad in [
            lambda: self.loan(rate=99),
            lambda: self.loan(tenure=0),
            lambda: self.loan(tenure=500),
            lambda: self.loan(principal=0),
            lambda: self.loan(status='vibes'),
            lambda: self.loan(start_date='nope'),
        ]:
            with self.assertRaises(ValueError):
                bad()

    def test_loans_are_scoped_per_user(self):
        self.loan()
        self.assertEqual(ledger.debt_summary('u2')['totals']['outstanding'], 0)


class NoMixing(LedgerCase):
    def test_ledger_holds_only_recorded_facts(self):
        """Forecasts live in the report. Nothing here may be a projection."""
        ledger.add_entry('u1', '2026-10-01', 'in', 2400, 'sales')
        summary = ledger.cash_summary('u1')
        self.assertNotIn('forecast', summary)
        self.assertNotIn('projection', summary)
        for entry in summary['entries']:
            self.assertNotIn('forecast', entry)


if __name__ == '__main__':
    unittest.main()
