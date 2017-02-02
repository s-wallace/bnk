import io
import datetime as dt
import unittest
from bnk import account
from bnk.__main__ import read_records
from bnk.parse import NonZeroSumError, read_bnk_data
from bnk.tests import recstrings
from bnk.tests import WriteCSVs
from bnk import groups


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

    def test_account_group_simple(self):
        accts = read_records(recstrings.a3t3b3a)
        perf = {}


        s = recstrings.a3t3b3b + "\ngroup ab -> (a b)\n"
        bnkdata = read_bnk_data(s)
        group = groups.Group('ab', [bnkdata['Account']['a'],
                                    bnkdata['Account']['b']])
        self.assertEqual(group, bnkdata['Group']['ab'])

        # try a meta account
        s2 = recstrings.a3t3b3b + "\nmeta ab -> (a b)\n"
        bnkdata = read_bnk_data(s2)
        meta = groups.MetaAccount('ab', [bnkdata['Account']['a'],
                                         bnkdata['Account']['b']])

        self.assertEqual(meta._transactions,
                         bnkdata['Meta']['ab']._transactions)


        # it should be ok to put the meta statement after the openings
        lines = recstrings.a3t3b3b.splitlines()
        lines.insert(3, "\nmeta ab -> (a b)\n")
        bnkdata = read_bnk_data("\n".join(lines))
        meta = groups.MetaAccount('ab', [bnkdata['Account']['a'],
                                         bnkdata['Account']['b']])
        mab = bnkdata['Meta']['ab']
        self.assertEqual(meta._transactions,
                         mab._transactions)

        # the meta account should have marked values at two places
        self.assertEqual(mab.get_value(dt.date(2001,12,31))[1], "Marked")
        self.assertEqual(mab.get_value(dt.date(2002,12,31))[1], "Marked")
        self.assertEqual(mab.get_value(dt.date(2002,3,31))[1], "No Data")

        actb = bnkdata['Account']['b']
        # account b should have marked balues at three places
        self.assertEqual(actb.get_value(dt.date(2001,12,31))[1], "Marked")
        self.assertEqual(actb.get_value(dt.date(2002,12,31))[1], "Marked")
        self.assertEqual(actb.get_value(dt.date(2002,3,31))[1], "Marked")
