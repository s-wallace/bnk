import datetime as dt
from bnk import reporting
from bnk.account import Period
from bnk.tables import flatten_table
from bnk.groups import MetaAccount
from bnk import fiscalyear as fy
from bnk import reporting

def report(args, bnkdata):

    periods = fy.standard_periods(args.date)
    # standard periods will give us too many, so loose a few
    periods.pop(3)
    periods.pop(3)

    accounts = [a for a in bnkdata['Account'].values()]

    report = reporting.PerfOverviewReport(accounts, periods)
    print(flatten_table(report, title="Performance Overview", banners=[0,1]))
    print("\n\n")
    report = reporting.BasicStatsReport(accounts, periods, 'gain')
    print(flatten_table(report, title="Gain Report", banners=[0,1]))

    report = reporting.BasicStatsReport(accounts, periods, 'net additions')
    print(flatten_table(report, title="Net Additions Report", banners=[0,1]))

    report = reporting.DetailReport(accounts[0], periods)
    print(flatten_table(report, title=report.name, banners=[0,1]))
