import math
import io
import datetime as dt
import unittest
from bnk import account
from bnk import read_records, read_bnk_data
from bnk.parse import NonZeroSumError
from bnk.tests import WriteCSVs
from bnk.tests import recstrings

class AccountTest(unittest.TestCase):

    def test_account_openclose(self):
        # Can't have an opening date on Jan 1, 1AD
        self.assertRaises(ValueError, account.Account, "test", dt.date(1,1,1))

        # Can't close an account before it's open
        a = account.Account("test", dt.date(2011,12,30))
        self.assertRaises(ValueError, a.set_closing, dt.date(2010,12,30))

        # Can't close an account twice
        a = account.Account("test", dt.date(2011,12,30))
        a.set_closing(dt.date(2012,10,31))
        self.assertRaises(ValueError, a.set_closing, dt.date(2012,12,30))

    def test_account_marksimple(self):

        # Can't mark at open or close
        a = account.Account("test", dt.date(2011,12,30))
        self.assertRaises(ValueError, a.mark_value, account.Value(dt.date(2011,12,30), 100))
        a.mark_value(account.Value(dt.date(2012,1,30), 200))
        a.mark_value(account.Value(dt.date(2012,10,31), 300))
        # Can't close where there's a non-zero mark
        self.assertRaises(ValueError, a.set_closing, dt.date(2012,10,31))
        a.set_closing(dt.date(2012,11,1))

        self.assertEqual(a.get_value(dt.date(2011,12,20)), (0.0, "Not Open"))
        self.assertEqual(a.get_value(dt.date(2011,12,30)), (0.0, "Marked"))
        self.assertEqual(a.get_value(dt.date(2012,1,30)), (200.0, "Marked"))
        self.assertEqual(a.get_value(dt.date(2012,10,31)), (300.0, "Marked"))
        self.assertEqual(a.get_value(dt.date(2012,11,1)), (0.0, "Marked"))
        self.assertEqual(a.get_value(dt.date(2012,11,2)), (0.0, "Closed"))
        self.assertTrue(math.isnan(a.get_value(dt.date(2012,10,1))[0]))
        self.assertEqual(a.get_value(dt.date(2012,10,1))[1], "No Data")

        a.carryvalues = dt.timedelta(days=400)
        self.assertEqual(a.get_value(dt.date(2012,10,1)),
                         (200.0, "Carried",
                          dt.date(2012,10,1)-dt.date(2012,1,30)))

        a.carryvalues = dt.timedelta(days=31)
        self.assertEqual(a.get_value(dt.date(2012,10,1))[1], "No Data")

        a = account.Account("test", dt.date(2011,12,30))
        a.mark_value(account.Value(dt.date(2012,10,31), 0))
        # Can close at a zero mark
        a.set_closing(dt.date(2012,10,31))


    def test_account_transactionsimple(self):
        a = account.Account("test", dt.date(2011,12,30))
        a.add_transaction(account.Transaction(dt.date(2012,1,1), dt.date(2012,1,31), 100))

        # Can't close in a transaction window
        self.assertRaises(ValueError, a.set_closing, dt.date(2012,1,10))

        # Can't mark a value during a transaction window
        self.assertRaises(ValueError, a.mark_value,
                          account.Value(dt.date(2012,1, 20), 50))

        # Mark *can* occur on the end date, but not the start
        a.mark_value(account.Value(dt.date(2012,1, 31), 100))
        self.assertRaises(ValueError, a.mark_value,
                          account.Value(dt.date(2012,1, 1), 50))

        # Can't add a transaction window if a marked value overlaps with it
        self.assertRaises(ValueError, a.add_transaction,
                          account.Transaction(dt.date(2012,1,1),
                                              dt.date(2012,2,1), 100))

        a.mark_value(account.Value(dt.date(2012,4,1), 200))

        # Can't add a transaction starting at a mark, but can add one ending at a mark
        self.assertRaises(ValueError, a.add_transaction,
                          account.Transaction(dt.date(2014,4,1), dt.date(2012,4,5), 50))
        a.add_transaction(account.Transaction(dt.date(2012,3,1), dt.date(2012,4,1), 20))

        # Can close at transaction window end
        a.add_transaction(account.Transaction(dt.date(2012,4,2), dt.date(2012,5,1), 20))
        a.set_closing(dt.date(2012,5,1))

        # Can add to a closed account
        a.add_transaction(account.Transaction(dt.date(2012,4,2), dt.date(2012,5,1), -50))


        # Can't add a transaction that spans the closing date
        self.assertRaises(ValueError, a.add_transaction,
                          account.Transaction(dt.date(2012,4,20), dt.date(2012,5,2), 100))


    def test_account_por(self):
        a = account.Account("test", dt.date(2011,12,30))
        a.add_transaction(account.Transaction(dt.date(2012,1,5), dt.date(2012,1,31), 100))
        a.add_transaction(account.Transaction(dt.date(2012,1,1), dt.date(2012,3,30), 100))
        a.add_transaction(account.Transaction(dt.date(2012,3,30), dt.date(2012,4,20), 100))
        a.add_transaction(account.Transaction(dt.date(2012,4,30), dt.date(2012,5,31), 100))
        a.mark_value(account.Value(dt.date(2012,5,31), 500))
        performance = {}
        tir = a.get_performance(None, None, performance)

        self.assertEqual(performance['start date'], dt.date(2011, 12, 30))
        self.assertEqual(performance['end date'], dt.date(2012, 5, 31))
        self.assertEqual(performance['additions'], 400)
        self.assertEqual(performance['subtractions'], 0)
        self.assertEqual(performance['gain'], 100)
        self.assertEqual(performance['carry'], 0)

    def test_parsesimple(self):
        recstr = """12-30-2001 open a
                    01-01-1900 open Assets

                    from 12-31-2001 until 12-31-2001
                    ---
                    Assets -> a  100

                    12-31-2001 balances
                    ---
                    a 100

                    12-31-2002 balances
                    ---
                    a 200
                    """

        accts = read_records(recstr)

        # check performance
        aperf = {}
        accts['a'].get_performance(None, None, aperf)
        self.assertEqual(aperf['start date'], dt.date(2001, 12, 30))
        self.assertEqual(aperf['end date'], dt.date(2002, 12, 31))
        self.assertEqual(aperf['additions'], 100)
        self.assertEqual(aperf['subtractions'], 0)
        self.assertEqual(aperf['gain'], 100)

        accts['a'].get_performance(None, dt.date(2001,12,31), aperf)
        self.assertEqual(aperf['start date'], dt.date(2001, 12, 30))
        self.assertEqual(aperf['end date'], dt.date(2001, 12, 31))
        self.assertEqual(aperf['additions'], 100)
        self.assertEqual(aperf['subtractions'], 0)
        self.assertEqual(aperf['gain'], 0)

        # Transactions must sum to zero...
        brknrecstr = """12-30-2001 open a
                    01-01-1900 open Assets

                    from 12-31-2001 until 12-31-2001
                    ---
                    a  100

                    12-31-2001 balances
                    ---
                    a 100

                    12-31-2002 balances
                    ---
                    a 200
                    """

        self.assertRaises(NonZeroSumError, read_records, brknrecstr)

        recstr = """12-30-2001 open a
                    01-01-1900 open Assets

                    from 12-31-2001 until 12-31-2001
                    ---
                    Assets -> a  100

                    12-31-2001 balances
                    ---
                    a 100

                    from 01-01-2002 until 12-31-2002
                    ---
                    Assets -> a  -50

                    12-31-2002 balances
                    ---
                    a 200
                    """
        accts = read_records(recstr)
        accts['a'].get_performance(None, None, aperf)
        self.assertEqual(aperf['start date'], dt.date(2001, 12, 30))
        self.assertEqual(aperf['end date'], dt.date(2002, 12, 31))
        self.assertEqual(aperf['additions'], 100)
        self.assertEqual(aperf['subtractions'], 50)
        self.assertEqual(aperf['gain'], 150)

        # parser doesn't hold state between read_records
        # 1. this is broken
        brkrecstr = """12-30-2001 open a
                       12-31-2001 open a"""
        self.assertRaises(ValueError, read_records, brkrecstr)
        # Using two calls to read_records should result in distinct accounts
        self.assertTrue(read_records, "12-30-2001 open a")
        self.assertTrue(read_records, "12-31-2001 open a")
        a = read_records('12-30-2001 open a')['a']
        b = read_records('12-31-2001 open a')['a']
        self.assertTrue(a != b)

    def test_parseonelines(self):
        recstr = """12-30-2001 open a
                    01-01-1900 open Assets

                    from 12-31-2001 until 12-31-2001 Assets -> a  100

                    12-31-2001 a 100

                    12-31-2002 a 200
                    """

        accts = read_records(recstr)

        # check performance
        aperf = {}
        accts['a'].get_performance(None, None, aperf)
        self.assertEqual(aperf['start date'], dt.date(2001, 12, 30))
        self.assertEqual(aperf['end date'], dt.date(2002, 12, 31))
        self.assertEqual(aperf['additions'], 100)
        self.assertEqual(aperf['subtractions'], 0)
        self.assertEqual(aperf['gain'], 100)
        irr = accts['a'].get_irr(None, None)

        accts['a'].get_performance(None, dt.date(2001,12,31), aperf)
        self.assertEqual(aperf['start date'], dt.date(2001, 12, 30))
        self.assertEqual(aperf['end date'], dt.date(2001, 12, 31))
        self.assertEqual(aperf['additions'], 100)
        self.assertEqual(aperf['subtractions'], 0)
        self.assertEqual(aperf['gain'], 0)

        recstr = """12-30-2001 open a
                    01-01-1900 open Assets

                    12-31-2001 Assets -> a  100

                    12-31-2001 a 100

                    12-31-2002 a 200
                    """

        accts = read_records(recstr)

        # check performance
        aperf = {}
        accts['a'].get_performance(None, None, aperf)
        self.assertEqual(aperf['start date'], dt.date(2001, 12, 30))
        self.assertEqual(aperf['end date'], dt.date(2002, 12, 31))
        self.assertEqual(aperf['additions'], 100)
        self.assertEqual(aperf['subtractions'], 0)
        self.assertEqual(aperf['gain'], 100)
        irr2 = accts['a'].get_irr(None, None)
        self.assertEqual(irr, irr2)

        accts['a'].get_performance(None, dt.date(2001,12,31), aperf)
        self.assertEqual(aperf['start date'], dt.date(2001, 12, 30))
        self.assertEqual(aperf['end date'], dt.date(2001, 12, 31))
        self.assertEqual(aperf['additions'], 100)
        self.assertEqual(aperf['subtractions'], 0)
        self.assertEqual(aperf['gain'], 0)

    def test_as_csv(self):
        recstr = """12-30-2001 open a
                    01-01-1900 open Assets

                    from 12-31-2001 until 12-31-2001
                    ---
                    Assets -> a  100

                    12-31-2001 balances
                    ---
                    a 100

                    12-31-2002 balances
                    ---
                    a 200
                    """
        accts = read_records(recstr)
        csv = io.StringIO()
        accts['a'].to_csv(csv)

        # Note, the columns dont sort unambiguously... so if there's an error
        # check that first...
        expectedcsv = (
            "12/30/2001,12/30/2001,0.0,,12/30/2001,0.0,0,12/30/2001,0.0,0"
            "\r\n"
            "12/31/2001,12/31/2001,,100.0,12/31/2001,100.0,0,12/31/2001,100.0,0"
            "\r\n"
            "12/31/2001,12/31/2001,100.0,,12/31/2001,,100.0,12/31/2001,,100.0"
            "\r\n"
            "12/31/2002,12/31/2002,200.0,,12/31/2002,200.0,0,12/31/2002,200.0,0"
            "\r\n")
        #print()
        #print(csv.getvalue())
        #print("--")
        #print(expectedcsv)
        self.assertEqual(expectedcsv, csv.getvalue())

    def test_performance(self):
        data = read_bnk_data(recstrings.a3t3b3b)

        perf = {}
        acctA = data['Account']['a']
        acctA.get_performance(dt.date(2001,12,31), dt.date(2002,12,31), perf)
        self.assertEqual(perf['carry'], 0)
        self.assertEqual(perf['start date'], dt.date(2001,12,31))
        self.assertEqual(perf['end date'], dt.date(2002,12,31))
        self.assertEqual(perf['subtractions'], 100)

        perf = {}
        # There's no value marked on 2002-3-31, so this is a problem
        self.assertRaises(ValueError, acctA.get_performance,
                          dt.date(2001,12,31), dt.date(2002,3,31), perf)

        # There's no value marked on 2002-6-30, so this is a problem
        self.assertRaises(ValueError, acctA.get_performance,
                          dt.date(2001,12,31), dt.date(2002,6,30), perf)

        acctA.carryvalues = dt.timedelta(days=300)
        # This will raise a ValueError since 2002-3-31 divides a transaction
        self.assertRaises(ValueError, acctA.get_performance,
                          dt.date(2001,12,31), dt.date(2002,3,31), perf)

        # 6-30 is ok, since it doesn't divide transactions
        acctA.get_performance(dt.date(2001,12,31), dt.date(2002,6,30), perf)
        self.assertEqual(perf['carry'], 181)
        self.assertEqual(perf['start date'], dt.date(2001,12,31))
        self.assertEqual(perf['end date'], dt.date(2002,6,30))
        self.assertEqual(perf['subtractions'], 100)
        self.assertEqual(perf['start balance'], 100)
        # and since we're carrying the balance from 12-31-2001 to 6-30-2002
        self.assertEqual(perf['start balance'], perf['end balance'])


    def test_range(self):

        # Range's are just tuples in disguise
        self.assertEqual(account.Range(3,5), (3,5))
        self.assertEqual("{:.2f}".format(account.Range(3,5)), "(3.00,5.00)")

if __name__ == "__main__":
    WriteCSVs = True
    unittest.main()
