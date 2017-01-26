import math
import datetime as dt
import unittest
from bnk import account
from bnk.__main__ import read_records
from bnk.parse import NonZeroSumError
from bnk import tables
import os
from bnk.tests import WriteCSVs

Verbose = 0
try:
    _v = int(os.environ['BNK_TEST_VERBOSITY'])
    Verbose = _v
except KeyError:
    pass


def show(args):
    global Verbose

    if Verbose:
        print(args)

class TableTest(unittest.TestCase):

    def test_table_simple(self):
        t = tables.Table(3, 3)
        t.set_header(['Name', 'Date', 'Value'])
        t.set_column(0, ['Fund A', 'Fund B', 'Fund C'])
        t.set_column(1, [dt.date(2010, 5, 1), dt.date(2012, 6, 1), dt.date(2011, 3, 1)])
        t.set_cell(0,2, 100.)
        t.set_cell(1,2, 150.)
        t.set_cell(2,2, 90.)

        table = t.content()
        self.assertEqual([['Name', 'Date', 'Value'],
                          ['Fund A', dt.date(2010,5,1), 100.],
                          ['Fund B', dt.date(2012,6,1), 150.],
                          ['Fund C', dt.date(2011,3,1), 90.]],
                         table)
        t = tables.Table(3,3)
        t.set_row(0,[1,2,3])
        t.set_row(1,[4,5,6])
        t.set_row(2,[7,8,9])

        self.assertEqual( [[1,2,3],[4,5,6],[7,8,9]], t.content() )
