import io
import datetime as dt
import unittest
from bnk import account
from bnk.__main__ import read_records
from bnk.parse import NonZeroSumError

WriteCSVs = False

class AccountIRRTest(unittest.TestCase):
    def test_irr_simple(self):
        r = """12-30-2000 open a
               12-30-2000 open b

               12-31-2000 balances
               ---
               a 0
               b 100

               from 01-01-2002 until 01-01-2002
               ---
               b -> a  12340000

               from 12-31-2002 until 12-31-2002
               ---
               a -> b  3620000

               01-01-2003 balances
               ---
               a 0 // this doesn't make a lot of sense, but is ok for the computations below

               from 12-31-2003 until 12-31-2003
               ---
               a -> b  5480000

               01-01-2004 balances
               ---
               a 0 // this doesn't make a lot of sense, but is ok for the computations below

               from 12-31-2004 until 12-31-2004
               ---
               a -> b  4810000

               01-01-2005 balances
               ---
               a  0

               01-02-2005 close a"""
        accts = read_records(r)
        if WriteCSVs:
            with open('test_irr-test_irr_simple-1-a.csv', 'w') as fout:
                accts['a'].to_csv(fout)
        irr = accts['a'].get_irr(dt.date(2000,12,31), dt.date(2005,1,1))
        irounded = (round(irr[0],3), round(irr[1], 3))
        # Using XIRR in LibreOffice
        self.assertEqual(irounded, (5.967, 5.967))



        r = """12-30-2000 open a
               12-30-2000 open b

               12-31-2000 balances
               ---
               a 0
               b 0

               from 01-01-2002 until 01-01-2002
               ---
               b -> a  100000

               from 01-01-2002 until 06-30-2002
               ---
               b -> a  50000

               12-31-2002 balances
               ---
               a 175000
        """
        accts = read_records(r)
        if WriteCSVs:
            with open('test_irr-test_irr_simple-2-a.csv', 'w') as fout:
                accts['a'].to_csv(fout)

        irr = accts['a'].get_irr(dt.date(2000,12,31), dt.date(2002,12,31))
        irounded = (round(irr[0],3), round(irr[1], 3))
        # Using XIRR in LibreOffice
        self.assertEqual(irounded, (16.716, 20.201))

    def test_irr_exact_timing(self):
        r = """12-30-2009 open a
               12-30-2000 open Assets

               12-31-2009 balances
               ---
               a 100000

               from 12-31-2010 until 12-31-2010
               ---
               Assets -> a  50000

               12-31-2010 balances
               ---
               a 160000
        """
        accts = read_records(r)
        irr = accts['a'].get_irr(dt.date(2009,12,31), dt.date(2010,12,31))
        irounded = (round(irr[0],5), round(irr[1], 5))
        # Using XIRR in LibreOffice (TEST 1)
        #  in test_irr_test_irr_exact_timing_1-3.ods
        self.assertEqual(irounded, (10.0, 10.0))

        r = """12-30-2009 open a
               12-30-2000 open Assets

               12-31-2009 balances
               ---
               a 100000

               12-31-2010 balances
               ---
               a 110000
        """
        accts = read_records(r)
        irr = accts['a'].get_irr(dt.date(2009,12,31), dt.date(2010,12,31))
        irounded = (round(irr[0],5), round(irr[1], 5))
        # Using XIRR in LibreOffice (TEST 2)
        #  in test_irr_test_irr_exact_timing_1-3.ods
        self.assertEqual(irounded, (10.0, 10.0))

        r = """12-30-2009 open a
               12-30-2000 open Assets

               12-31-2009 balances
               ---
               a 100000

               from 12-30-2010 until 12-30-2010
               ---
               Assets -> a  50000

               12-31-2010 balances
               ---
               a 160000
        """
        accts = read_records(r)
        irr = accts['a'].get_irr(dt.date(2009,12,31), dt.date(2010,12,31))
        irounded = (round(irr[0],5), round(irr[1], 5))
        # Using XIRR in LibreOffice (TEST 3)
        #  in test_irr_test_irr_exact_timing_1-3.ods
        self.assertEqual(irounded, (9.98696, 9.98696))

        r = """12-30-2009 open a
               12-30-2000 open Assets

               12-31-2009 balances
               ---
               a 100000

               from 12-30-2010 until 12-31-2010
               ---
               Assets -> a  50000

               12-31-2010 balances
               ---
               a 160000
        """
        accts = read_records(r)
        irr = accts['a'].get_irr(dt.date(2009,12,31), dt.date(2010,12,31))
        irounded = (round(irr[0],5), round(irr[1], 5))
        # Using XIRR in LibreOffice (combined tests 1 and 3)
        #  in test_irr_test_irr_exact_timing_1-3.ods
        self.assertEqual(irounded, (9.98696, 10))


    def test_irr_with_overlap(self):
        r = """12-30-2000 open a
               12-30-2000 open b

               12-31-2000 balances
               ---
               a 0
               b 0

               from 01-01-2002 until 06-30-2002
               ---
               b -> a  50000

               from 02-01-2002 until 03-31-2002
               ---
               b -> a  50000

               from 03-01-2002 until 04-01-2002
               ---
               b -> a  50000

               06-30-2002 balances
               ---
               a  120000

               12-31-2002 balances
               ---
               a  175000
        """
        accts = read_records(r)
        if WriteCSVs:
            with open('test_irr-test_irr_with_overlap-1-a.csv', 'w') as fout:
                accts['a'].to_csv(fout)

        irr = accts['a'].get_irr(dt.date(2000,12,31), dt.date(2002,12,31))
        irounded = (round(irr[0],3), round(irr[1], 3))
        # Using XIRR in LibreOffice (TEST 1)
        self.assertEqual(irounded, (18.34, 25.828))

        irr = accts['a'].get_irr(dt.date(2000,12,31), dt.date(2002,6,30))
        irounded = (round(irr[0],3), round(irr[1], 3))
        # Using XIRR in LibreOffice (TEST 2)
        self.assertEqual(irounded, (-76.272, -41.99))


if __name__ == "__main__":
    WriteCSVs = True
    unittest.main()
