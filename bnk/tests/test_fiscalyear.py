import io
import datetime as dt
import unittest
from bnk import account
from bnk.__main__ import read_records
from bnk.parse import NonZeroSumError
import bnk.fiscalyear as fy
from bnk.tests import WriteCSVs

class FYTest(unittest.TestCase):

    def test_fy_quarter_ends(self):

        quarters = [q for q in fy.quarters(dt.date(2012,12,31),
                                           dt.date(2013,12,31))]

        self.assertEqual([
            account.Period(dt.date(2012,9,30), dt.date(2012,12,31), "Q4-2012"),
            account.Period(dt.date(2012,12,31), dt.date(2013,3,31), "Q1-2013"),
            account.Period(dt.date(2013,3,31), dt.date(2013,6,30), "Q2-2013"),
            account.Period(dt.date(2013,6,30), dt.date(2013,9,30), "Q3-2013"),
            account.Period(dt.date(2013,9,30), dt.date(2013,12,31), "Q4-2013")],
                         quarters)


        self.assertEqual([q.name for q in quarters],
                          [fy.name_of_quarter(q.end) for q in quarters])

        # check that end_of_quarter returns , e.g., 3,31,12 for both
        # 1-1-2012 and 3-31-2012
        self.assertEqual([q.end for q in quarters],
                         [fy.end_of_quarter(q.start + dt.timedelta(days=1))
                          for q in quarters])

        self.assertEqual([q.end for q in quarters],
                         [fy.end_of_quarter(q.end) for q in quarters])

        # check that end_of_completed_quarter returns , e.g., 3,31,12 for both
        # 3-31-2012 and 6-29-2012
        self.assertEqual([q.start for q in quarters],
                         [fy.end_of_completed_quarter(q.start)
                          for q in quarters])

        self.assertEqual([q.start for q in quarters],
                         [fy.end_of_completed_quarter(q.end - dt.timedelta(days=1))
                          for q in quarters])
