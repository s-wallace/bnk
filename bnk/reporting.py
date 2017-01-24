from bnk.tables import *

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
                    print(act.name, period, "Exception--", E, type(E))
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
            print("Couldn't find min/max")
            print(E)

        self._table = table
        self._periods = periods

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
            for period in periods:
                try:
                    perf = {}
                    act.get_performance(period.start, period.end, perf)
                    row.append(Cell(perf[attribute], fmt="{: ,.2f}"))
                except Exception as E:
                    row.append(Cell(None, f=0, s='---'))
            table.set_row(i, row)
        self._table = table
        self._periods = periods

        f = ['Total:']
        for columni in range(len(periods)):
            f.append(Cell(sum([c for c in self._table.column(columni+1)]), fmt='{: ,.2f}'))
        self._table.set_footer(f)

    def content(self):

        s = StringView(self._table,
                       hfmts=['{:<30s}'] + ['{:>15s}']*len(self._periods),
                       cfmts=['{:<30s}'] + ['{:>15s}']*len(self._periods))

        return s.content()

