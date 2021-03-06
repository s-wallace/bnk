"""An example ASCII report."""
import datetime as dt

from bnk import reporting
from bnk.views import AsciiView
from bnk import fiscalyear as fy


def report(args, bnkdata):
    """Generate the report."""

    periods = fy.standard_periods(dt.date(2016, 12, 31))
    nwdates = [dt.date(2016, 12, 31), dt.date(2015, 12, 31),
               dt.date(2014, 12, 31)]

    group = bnkdata['Group']
    with AsciiView() as ascii:
        if 'R_networth' in group:
            report = reporting.NetWorthReport(group['R_networth'], nwdates)
            ascii.append(report, title="Net Worth Report")

        if 'R_performance' in group:
            report = reporting.PerfOverviewReport(group['R_performance'],
                                                  periods)
            ascii.append(report, title="Performance Overview Report")

        if 'R_basicstats' in group:
            report = reporting.BasicStatsReport(group['R_basicstats'],
                                                periods, 'net additions')
            ascii.append(report, title="Net Additions Report")

            report = reporting.BasicStatsReport(group['R_basicstats'],
                                                periods, 'gain')
            ascii.append(report, title="Gain Report")

        if 'R_detail' in group:
            for account in group['R_detail']:
                report = reporting.DetailReport(account, periods)
                ascii.append(report, title=report.name)
