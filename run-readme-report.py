#!/usr/bin/env python3
"""Display Records and Reports for the README.md file."""

from bnk.tests import recstrings
from bnk import read_bnk_data
from bnk.account import Period
from bnk import reporting
from bnk.views import AsciiView
import datetime as dt


class _N(object):
    pass

print("-- RECORDS --")
readme = "\n".join([r.strip() for r in recstrings.readme.splitlines()])
print(readme)
print("\n\n")

bnkdata = read_bnk_data(readme)

print("-- REPORT --")
args = _N()
args.date = dt.date(2002, 12, 31)
periods = [Period(dt.date(2001, 12, 31), dt.date(2002, 12, 31), '2002'),
           Period(dt.date(2000, 12, 31), dt.date(2001, 12, 31), '2001'),
           Period(None, None, 'Lifetime')]

accounts = [a for a in bnkdata['Account'].values() if a.name not in ['Assets']]

with AsciiView() as ascii:

    report = reporting.PerfOverviewReport(accounts, periods)
    ascii.append(report, title="Performance Overview")

    report = reporting.BasicStatsReport(accounts, periods, 'gain')
    ascii.append(report, title="Gain Report")

    report = reporting.BasicStatsReport(accounts, periods, 'net additions')
    ascii.append(report, title="Net Additions Report")

    report = reporting.DetailReport(accounts[0], periods)
    ascii.append(report, title=report.name)
