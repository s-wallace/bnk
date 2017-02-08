import logging
from bnk.tables import *
from bnk.groups import Group
import datetime as dt

_log = logging.getLogger(__name__)

class PerfOverviewReport(object):

    def __init__(self, accounts, periods, name="Performance Overview Report"):
        table = Table(len(accounts), len(periods)+1)
        header = ["Account"] + [p.name for p in periods]
        table.set_header(header)
        for (i, act) in enumerate(accounts):
            row = [act.name]
            for period in periods:
                try:
                    row.append(Cell(act.get_irr(period.start, period.end), fmt="{: 6.2f}"))
                except Exception as E:
                    row.append(Cell(None, f=0, s="---"))
                    _log.debug("Empty cell: %s %s %s -> %s",name, act.name, period, E)
            table.set_row(i, row)

        try:
            for i in range(0, len(periods)):
                cmin = min([c.object()[0] for c in table.column(i+1) if c.object()])
                cmax = max([c.object()[1] for c in table.column(i+1) if c.object()])
                for cell in table.column(i+1):
                    if cell.object():
                        if cell.object()[0] == cmin:
                            cell.meta['min'] = True
                        if cell.object()[1] == cmax:
                            cell.meta['max'] = True
        except Exception as E:
            _log.debug("Couldn't find min/max")

        table.set_column_formats( [CF('<', 30)] + [CF('>',20)]*len(periods) )

        self.table = table

class NetWorthReport(object):
    """NetWorthReport shows total value across accounts on set of dates"""

    def __init__(self, accounts, dates, name="NetWorth Report"):
        """Initialize the NetWorthReport:

        Arguments:
         accounts : a list of accounts and/or Groups to include in the report
         dates : a list of dates on which the total value should be calculated
        """

        self.table = self._make_nw_table(accounts, dates)

    def _make_nw_table(self, accounts, dates, depth=0):
        """recursively build the networth table, a subtable is built
        for each group."""

        table = Table(len(accounts), len(dates)+1)

        if not depth:
            name = 'Accounts'
        else:
            name = accounts._name

        header = [name] + ["{:%Y-%m-%d}".format(d) for d in dates]
        table.set_header(header)

        for (i, act) in enumerate(accounts):
            if isinstance(act, Group):
                row = self._make_nw_table(act, dates, depth+1)
            else:
                row = [act.name]
                maxcarry = 0
                for date in dates:
                    try:
                        perf = {}
                        act.get_performance(date, date, perf)
                        meta = {}
                        if perf['carry'] > maxcarry:
                            c = perf['carry']
                            meta['carry'] = c
                            if c > maxcarry:
                                maxcarry = c
                        row.append(Cell(perf['start balance'],
                                        fmt="{: ,.2f}", meta=meta))

                    except Exception as E:
                        row.append(Cell(None, f=0, s='---'))
                        _log.debug("Empty cell: %s %s -> %s", act.name, date, E)

                if maxcarry:
                    row[0] = act.name + " [c%d]"%(maxcarry)
            table.set_row(i, row)

        if depth == 0:
            f = ['Total:']
        else:
            f = ['SubTotal:']

        for columni in range(len(dates)):
            # sum across all entries in the table/subtables
            # ignore headers and footers
            f.append(Cell(sum([c for c in
                               table.column(columni+1, False, False, True)]),
                          fmt='{: ,.2f}'))

        table.set_footer(f)
        table.set_column_formats( [CF('<', 30)] + [CF('>',15)]*len(dates) )
        return table

class BasicStatsReport(object):

    def __init__(self, accounts, periods, attribute, name="Performance Overview Report"):
        assert attribute in ['gain', 'additions', 'subtractions', 'net additions']

        table = Table(len(accounts), len(periods)+1)
        header = ["Account"] + [p.name for p in periods]
        table.set_header(header)
        for (i, act) in enumerate(accounts):
            row = [act.name]
            maxcarry = 0
            for period in periods:
                try:
                    perf = {}
                    act.get_performance(period.start, period.end, perf)
                    meta = {}
                    if perf['carry'] > maxcarry:
                        c = perf['carry']
                        meta['carry'] = c
                        if c > maxcarry:
                            maxcarry = c
                    row.append(Cell(perf[attribute], fmt="{: ,.2f}", meta=meta))

                except Exception as E:
                    row.append(Cell(None, f=0, s='---'))
                    _log.debug("Empty cell: %s %s %s -> %s",name, act.name, period, E)

            if maxcarry:
                row[0] = act.name + " [c%d]"%(maxcarry)
            table.set_row(i, row)

        f = ['Total:']
        for columni in range(len(periods)):
            f.append(Cell(sum([c for c in table.column(columni+1)]), fmt='{: ,.2f}'))
        table.set_footer(f)
        table.set_column_formats( [CF('<', 30)] + [CF('>',15)]*len(periods) )
        self.table = table


class DetailReport(object):

    def __init__(self, account, periods, name=None):
        if not name:
            name = "{:s} --  Detail Report over the lifetime {:%Y-%m-%d} to {:%Y-%m-%d}".format(
                account.name, account._topen, account._values[-1].t)
        self.name = name

        table = Table(len(periods), 8)
        header = ["Period", "Start Date", "Performance", "Adds", "Subs", "St. Value", "End Value", "Gain"]
        table.set_header(header)
        for i,period in enumerate(periods):
            row = [period.name]
            perf = {}
            try:
                account.get_performance(period.start, period.end, perf)
                row.append(Cell(perf['start date'], fmt="{:%Y-%m-%d}"))
                row.append(Cell(perf['irr'], fmt="{: .2f}"))
                row.append(Cell(perf['additions'], fmt="{: ,.2f}"))
                row.append(Cell(perf['subtractions'], fmt="{: ,.2f}"))
                row.append(Cell(perf['start balance'], fmt="{: ,.2f}"))
                row.append(Cell(perf['end balance'], fmt="{: ,.2f}"))
                row.append(Cell(perf['gain'], fmt="{: ,.2f}"))

                if perf['carry'] != 0:
                    row[0] = row[0] + ' [c%d]'%(perf['carry'])
            except Exception as E:
                while len(row) < 8:
                    row.append(Cell(None, f=0, s="---"))
                _log.debug("Empty row: %s %s %s -> %s",name, account.name, period, E)

            table.set_row(i, row)

        table.set_column_formats( [CF('<', 18)]*2+[CF('>', 18)]*6 )
        self.table = table
