"""Tests for bnk.groups module."""

import datetime as dt
import unittest
from bnk.parse import read_bnk_data
from bnk.tests import recstrings
from bnk.tests import WriteCSVs
from bnk import groups


class GroupingTest(unittest.TestCase):
    """Test cases for bnk.groups module."""

    def test_group_meta_simple(self):
        """Verify metrics for meta accounts.

        Metrics for meta accounts should correspond to metrics
        for contributing accounts.
        """
        accts = read_bnk_data(recstrings.a3t3b3a)['Account']
        aperf = {}
        accts['a'].get_performance(None, None, aperf)
        self.assertEqual(aperf['additions'], 200)
        self.assertEqual(aperf['subtractions'], 100)
        self.assertEqual(aperf['gain'], 100)
        irounded = (round(aperf['irr'][0], 3), round(aperf['irr'][1], 3))
        # Using XIRR in LibreOffice
        self.assertEqual(irounded, (56.314, 86.433))

        bperf = {}
        accts['b'].get_performance(None, None, bperf)
        self.assertEqual(bperf['additions'], 250)
        self.assertEqual(bperf['subtractions'], 0)
        self.assertEqual(bperf['gain'], 50)
        irounded = (round(bperf['irr'][0], 3), round(bperf['irr'][1], 3))
        # Using XIRR in LibreOffice
        self.assertEqual(irounded, (21.131, 22.327))

        m = groups.MetaAccount('meta', [accts['a'], accts['b']])
        mperf = {}
        m.get_performance(None, None, mperf)
        for k in ['gain', 'additions', 'subtractions']:
            self.assertEqual(mperf[k], aperf[k] + bperf[k])

        # it's not as simple to figure out the performance, so
        # we need to do that in LibreOffice
        irounded = (round(mperf['irr'][0], 3), round(mperf['irr'][1], 3))
        # Using XIRR in LibreOffice
        self.assertEqual(irounded, (36.339, 44.469))

        if WriteCSVs:
            with open('test_grouping-meta_simple-a.csv', 'w') as fout:
                accts['a'].to_csv(fout)

            with open('test_grouping-meta_simple-b.csv', 'w') as fout:
                accts['b'].to_csv(fout)

            with open('test_grouping-meta_simple-meta.csv', 'w') as fout:
                m.to_csv(fout)

    def test_group_creation(self):
        """Verify groups/meta-accounts created via code/parser are equal."""

        # it should be equivilant to make the group via parser, or in code
        s = recstrings.a3t3b3b + "\ngroup ab -> (a b)\n"
        bnkdata = read_bnk_data(s)
        group = groups.Group('ab', [bnkdata['Account']['a'],
                                    bnkdata['Account']['b']])
        self.assertEqual(group, bnkdata['Group']['ab'])

        # it should be equivilant to make a meta-account via parser, or in code
        s2 = recstrings.a3t3b3b + "\nmeta ab -> (a b)\n"
        bnkdata = read_bnk_data(s2)
        meta = groups.MetaAccount('ab', [bnkdata['Account']['a'],
                                         bnkdata['Account']['b']])

        self.assertEqual(meta._transactions,
                         bnkdata['Meta']['ab']._transactions)

        # it should be ok to put the meta statement after accounts are
        # opened, whereas above we did it at the end of the file
        lines = recstrings.a3t3b3b.splitlines()
        lines.insert(3, "\nmeta ab -> (a b)\n")
        bnkdata = read_bnk_data("\n".join(lines))
        meta = groups.MetaAccount('ab', [bnkdata['Account']['a'],
                                         bnkdata['Account']['b']])
        mab = bnkdata['Meta']['ab']
        self.assertEqual(meta._transactions,
                         mab._transactions)

    def test_meta_value_marks(self):
        """Verify that meta account marks values appropriately."""

        lines = recstrings.a3t3b3b.splitlines()
        lines.insert(3, "\nmeta ab -> (a b)\n")
        bnkdata = read_bnk_data("\n".join(lines))
        mab = bnkdata['Meta']['ab']

        # the meta account should have marked values at two places
        self.assertEqual(mab.get_value(dt.date(2001, 12, 31))[1], "Marked")
        self.assertEqual(mab.get_value(dt.date(2002, 12, 31))[1], "Marked")
        self.assertEqual(mab.get_value(dt.date(2002, 3, 31))[1], "No Data")

        actb = bnkdata['Account']['b']
        # account b should have marked balues at three places
        self.assertEqual(actb.get_value(dt.date(2001, 12, 31))[1], "Marked")
        self.assertEqual(actb.get_value(dt.date(2002, 12, 31))[1], "Marked")
        self.assertEqual(actb.get_value(dt.date(2002, 3, 31))[1], "Marked")
