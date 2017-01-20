import datetime as dt
import unittest
from bnk import account


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
        
