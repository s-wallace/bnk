#!/usr/bin/env python3

from bnk.tests import recstrings, samplereport
from bnk import read_bnk_data
from bnk.account import Period
from bnk import reporting
from bnk.tables import flatten_table
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
args.date = dt.date(2002,12,31)
periods = [Period(dt.date(2001,12,31), dt.date(2002,12,31), '2002'),
           Period(dt.date(2000,12,31), dt.date(2001,12,31), '2001'),
           Period(None, None, 'Lifetime')]


accounts = [a for a in bnkdata['Account'].values() if a.name not in ['Assets']]
report = reporting.PerfOverviewReport(accounts, periods)
print(flatten_table(report, title="Performance Overview"))
print("\n\n")
report = reporting.BasicStatsReport(accounts, periods, 'gain')
print(flatten_table(report, title="Gain Report"))

report = reporting.BasicStatsReport(accounts, periods, 'net additions')
print(flatten_table(report, title="Net Additions Report"))


report = reporting.DetailReport(accounts[0], periods)
print(flatten_table(report, title=report.name))
