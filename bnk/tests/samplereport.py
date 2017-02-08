import datetime as dt
from bnk import reporting
from bnk.account import Period
from bnk.views import ascii_view
from bnk.groups import MetaAccount
from bnk import fiscalyear as fy
from bnk import reporting

def report(args, bnkdata):

    periods = fy.standard_periods(args.date)


    accounts = [a for a in bnkdata['Account'].values()]

    report = reporting.PerfOverviewReport(accounts, periods)
    print(ascii_view(report, title="Performance Overview"))
    print("\n\n")
    report = reporting.BasicStatsReport(accounts, periods, 'gain')
    print(ascii_view(report, title="Gain Report"))

    report = reporting.BasicStatsReport(accounts, periods, 'net additions')
    print(ascii_view(report, title="Net Additions Report"))

    report = reporting.DetailReport(accounts[0], periods)
    print(ascii_view(report, title=report.name))
