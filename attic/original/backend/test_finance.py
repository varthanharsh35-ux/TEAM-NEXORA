import unittest
from decimal import Decimal
from finance import calculate

class FinanceTests(unittest.TestCase):
    def test_required_example(self):
        r=calculate(100000,'2026-01-31')
        self.assertEqual((r['project_cost'],r['loan'],r['scheme']),(1000000,900000,'term'))
        self.assertEqual(len(r['schedule']),28)
        self.assertTrue(all(x['payment']==0 for x in r['schedule'][:2]))
        self.assertEqual(r['schedule'][2]['month'],9)
        self.assertEqual(r['schedule'][-1]['due_date'],'2033-01-31')
    def test_threshold_and_cap(self):
        r=calculate(14000)
        self.assertEqual((r['scheme'],r['loan'],r['funding_gap']),('micro',125000,1000))
        self.assertEqual(r['schedule'][1]['month'],6)
        self.assertEqual(len(r['schedule']),12)
        self.assertEqual(calculate(14000.01)['scheme'],'term')
        self.assertEqual(calculate(500000)['loan'],4500000)
        self.assertEqual(calculate(500000.01)['scheme'],'outside')
    def test_invalid(self):
        for x in [0,-1,'x',None,'NaN','Infinity',True,0.001,100000001]:
            with self.subTest(x=x),self.assertRaises(ValueError):calculate(x)
    def test_conservation(self):
        for x in [1,100,13999,14000,14001,100000,500000]:
            r=calculate(x)
            self.assertEqual(r['schedule'][-1]['balance'],0)
            payments=sum(Decimal(str(z['payment'])) for z in r['schedule'])
            self.assertEqual(payments,Decimal(str(r['total_repayment'])))
            self.assertAlmostEqual(r['total_repayment']-r['loan'],r['total_interest'],places=6)
            self.assertTrue(all(z['balance']>=0 for z in r['schedule']))
    def test_leap(self):
        self.assertEqual(calculate(1000,'2023-11-30')['schedule'][0]['due_date'],'2024-02-29')

if __name__=='__main__':unittest.main()
