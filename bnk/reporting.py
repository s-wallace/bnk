import logging
from bnk.tables import *
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
                        if cell.object()[0] == cmin: cell.meta = 'min'
                        if cell.object()[1] == cmax: cell.meta = 'max'
        except Exception as E:
            _log.debug("Couldn't find min/max")

        self._table = table
        self._periods = periods

    def has_footer(self):
        return False
    def has_header(self):
        return True

    def content(self):
        def minmax(cell):
            if cell.meta == "min": return "v " + cell._s
            elif cell.meta == "max": return "^ " + cell._s
            else: return cell._s

        self._table.restring(cfmts=[None] + [minmax]*len(self._periods))

        s = StringView(self._table,
                       hfmts=['{:<30s}'] + ['{:>20s}']*len(self._periods),
                       cfmts=['{:<30s}'] + ['{:>20s}']*len(self._periods))

        return s.content()

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
                    c = perf['carry']
                    if c > maxcarry:
                        maxcarry = c
                    row.append(Cell(perf[attribute],
                                    fmt="{: ,.2f}'" if c else "{: ,.2f} "))

                except Exception as E:
                    row.append(Cell(None, f=0, s='---'))
                    _log.debug("Empty cell: %s %s %s -> %s",name, act.name, period, E)

            if maxcarry:
                row[0] = act.name + " [c%d]"%(maxcarry)
            table.set_row(i, row)
        self._table = table
        self._periods = periods

        f = ['Total:']
        for columni in range(len(periods)):
            f.append(Cell(sum([c for c in self._table.column(columni+1)]), fmt='{: ,.2f} '))
        self._table.set_footer(f)

    def has_footer(self):
        return True
    def has_header(self):
        return True

    def content(self):

        s = StringView(self._table,
                       hfmts=['{:<30s}'] + ['{:>15s}']*len(self._periods),
                       cfmts=['{:<30s}'] + ['{:>15s}']*len(self._periods))

        return s.content()


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

        self._table = table
        self._periods = periods

    def has_footer(self):
        return False
    def has_header(self):
        return True

    def content(self):
        print("Table width", self._table._cols)
        s = StringView(self._table,
                       hfmts=['{:<18s}']*8,
                       cfmts=['{:<18s}']*8)

        return s.content()
