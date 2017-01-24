import io
import datetime as dt
import unittest
from bnk import account
from bnk.__main__ import read_records
from bnk.parse import NonZeroSumError
from bnk.tests import recstrings
from bnk import groups

WriteCSVs = True

class GroupingTest(unittest.TestCase):

    def test_account_meta_simple(self):

        accts = read_records(recstrings.a3t3b3a)
        perf = {}
        accts['a'].get_performance(None, None, perf)
        self.assertEqual(perf['additions'], 200)
        self.assertEqual(perf['subtractions'], 100)
        self.assertEqual(perf['gain'], 100)
        irounded = (round(perf['irr'][0],3), round(perf['irr'][1], 3))
        # Using XIRR in LibreOffice
        self.assertEqual(irounded, (56.314, 86.433))

        perf = {}
        accts['b'].get_performance(None, None, perf)
        self.assertEqual(perf['additions'], 250)
        self.assertEqual(perf['subtractions'], 0)
        self.assertEqual(perf['gain'], 50)
        irounded = (round(perf['irr'][0],3), round(perf['irr'][1], 3))
        # Using XIRR in LibreOffice
        self.assertEqual(irounded, (21.131, 22.327))

        m = groups.MetaAccount('meta', [accts['a'], accts['b']])
        perf = {}
        m.get_performance(None, None, perf)
        self.assertEqual(perf['gain'], 150.0)
        self.assertEqual(perf['additions'], 450)
        self.assertEqual(perf['subtractions'], 100)
        irounded = (round(perf['irr'][0],3), round(perf['irr'][1], 3))
        # Using XIRR in LibreOffice
        self.assertEqual(irounded, (36.339, 44.469))


        if WriteCSVs:
            with open('test_grouping-meta_simple-a.csv', 'w') as fout:
                accts['a'].to_csv(fout)

            with open('test_grouping-meta_simple-b.csv', 'w') as fout:
                accts['b'].to_csv(fout)

            with open('test_grouping-meta_simple-meta.csv', 'w') as fout:
                m.to_csv(fout)