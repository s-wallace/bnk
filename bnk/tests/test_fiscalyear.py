import io
import datetime as dt
import unittest
from bnk import account
from bnk.__main__ import read_records
from bnk.parse import NonZeroSumError
import bnk.fiscalyear as fy

WriteCSVs = False

class FYTest(unittest.TestCase):

    def test_fy_quarter_ends(self):

        qe = [q for q in fy.quarter_ends(dt.date(2012,12,31), dt.date(2013,12,31))]
        self.assertEqual([dt.date(2012,12,31),
                          dt.date(2013,3,31),
                          dt.date(2013,6,30),
                          dt.date(2013,9,30),
                          dt.date(2013,12,31)], qe)

        qnames = [fy.quarter_name(q) for q in qe]
        self.assertEqual(['Q4-2012', 'Q1-2013', 'Q2-2013', 'Q3-2013', 'Q4-2013'], qnames)
