"""Reports for bnk data."""

import logging
from bnk.tables import Cell, CF, Table
from bnk.groups import Group
import subprocess

_log = logging.getLogger(__name__)


class VersionReport(object):
    """Displays information about the version of the codebase and records.

    Rows show specific version information including:
     - git version of bnk code
     - last log message from git
     - (optionally) enforces that bnk has no working modifications
    """

    def __init__(self, cmdline, files=[], strict=False):
        """Initialize the VersionReport.

        Arguments:
         cmdline - the command line used to launch bnk
         files   - a list of files passed as input
         strict  - ensure bnk has no modifications to working copy
        """
        table = Table(0, 1, growable=True)
        row = 0

        def newrow():
            nonlocal row
            oldrow = row
            row += 1
            table.addrow()
            return oldrow

        if strict:
            output = subprocess.check_output('git status -s', shell=True)
            output = output.strip()
            if output:
                raise Exception("git status indicates a commit is required")

            strictchk = ('strict checking -- working directory '
                         'contains no modifications')
            table.set_cell(newrow(), 0, strictchk)

            output = subprocess.check_output('git log -n1', shell=True)
            for l in output.split('\n'):
                table.set_cell(newrow(), 0, '    ' + l)

        else:
            output = subprocess.check_output('git status -s', shell=True)
            output = output.strip()
            if not output:
                nomods = ' -- working directory contains no modifications'
                table.set_cell(newrow(), 0, nomods)

                output = subprocess.check_output('git log -n1', shell=True)
                for l in output.split('\n'):
                    table.set_cell(newrow(), 0, '    ' + l)

            else:
                table.set_cell(newrow(), 0,
                               ' -- working directory contains modifications')

                for f in files:
                    table.set_cell(newrow(), 0, f)
                    output = subprocess.check_output('git log -n1 %s' % (f),
                                                     shell=True)
                    for l in output.split('\n'):
                        table.set_cell(newrow(), 0, ('    ' + l))

        table.set_column_formats([CF('<', 50)])
        self.table = table


class PerfOverviewReport(object):
    """Displays the performace of accounts for the given periods.

    Accounts are placed in rows, periods are placed in columns. Each
    cell contains the performance (internal rate of return) of the given
    account for the given period.

    Cell metadata:
     'min':True - the lowest performing account for the given period (column)
     'max':True - the highest performing account for the given period
    """

    def __init__(self, accounts, periods, name="Performance Overview Report"):
        """Initialize the PerfOverviewReport.

        Arguments:
         accounts : a list of accounts and/or Groups to include in the report
         periods : a list of periods on which the IRR should be calculated
        """

        table = Table(len(accounts), len(periods) + 1)
        header = ["Account"] + [p.name for p in periods]
        table.set_header(header)
        for (i, act) in enumerate(accounts):
            row = [act.name]
            for period in periods:
                try:
                    row.append(Cell(act.get_irr(period.start, period.end),
                                    fmt="{: 6.2f}"))

                except Exception as E:
                    row.append(Cell(None, f=0, s="---"))
                    _log.debug("Empty cell: %s %s %s -> %s", name,
                               act.name, period, E)
            table.set_row(i, row)

        try:
            for i in range(0, len(periods)):
                cmin = min([c.object()[0]
                            for c in table.column(i + 1) if c.object()])
                cmax = max([c.object()[1]
                            for c in table.column(i + 1) if c.object()])
                for cell in table.column(i + 1):
                    if cell.object():
                        if cell.object()[0] == cmin:
                            cell.meta['min'] = True
                        if cell.object()[1] == cmax:
                            cell.meta['max'] = True
        except Exception as E:
            _log.debug("Couldn't find min/max")

        table.set_column_formats([CF('<', 30)] + [CF('>', 20)]*len(periods))

        self.table = table


class NetWorthReport(object):
    """Displays the total value across accounts on a set of dates.

    Accounts are placed in rows, dates are placed in columns. Each cell
    contains the account value on the specified date.  A footer shows the
    column sum. Groups are subtotaled nested tables.

    Cell metadata:
     'carry': the number of days the balance was carried to produce the given
               result (only appears if value is non-zero).

    Annotations:
     if an account had carried values reported, the account name has a string:
     '[cX]' appended which indicates the longest carry (maximum number of
     days for which the information is out of date).
    """

    def __init__(self, accounts, dates, name="NetWorth Report"):
        """Initialize the NetWorthReport.

        Arguments:
         accounts : a list of accounts and/or Groups to include in the report
         dates : a list of dates on which the total value should be calculated
        """

        self.table = self._make_nw_table(accounts, dates)

    def _make_nw_table(self, accounts, dates, depth=0):
        """Recursively build the networth table.

        A subtable is built for each group.
        """

        table = Table(len(accounts), len(dates) + 1)

        if not depth:
            name = 'Accounts'
        else:
            name = accounts._name

        header = [name] + ["{:%Y-%m-%d}".format(d) for d in dates]
        table.set_header(header)

        for (i, act) in enumerate(accounts):
            if isinstance(act, Group):
                row = self._make_nw_table(act, dates, depth + 1)
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
                        _log.debug("Empty cell: %s %s -> %s", act.name,
                                   date, E)

                if maxcarry:
                    row[0] = act.name + " [c%d]" % (maxcarry)
            table.set_row(i, row)

        if depth == 0:
            f = ['Total:']
        else:
            f = ['SubTotal:']

        for columni in range(len(dates)):
            # sum across all entries in the table/subtables
            # ignore headers and footers
            f.append(Cell(sum([c for c in
                               table.column(columni + 1, False, False, True)]),
                          fmt='{: ,.2f}'))

        table.set_footer(f)
        table.set_column_formats([CF('<', 30)] + [CF('>', 15)]*len(dates))
        return table


class BasicStatsReport(object):
    """Displays one statistic across a set of accounts and periods.

    Periods are placed in columns, Accounts are placed in rows. Each
    cell contains the statistic of interest for the corresponding
    account/period.

    Cell metadata:
     'carry': the number of days the balance was carried to produce the given
               result (only appears if value is non-zero).

    Annotations:
     if an account had carried values reported, the account name has a string:
     '[cX]' appended which indicates the longest carry (maximum number of
     days for which the information is out of date).

    """

    def __init__(self, accounts, periods, attribute,
                 name="Performance Overview Report"):
        """Initialize the Basic Stats Report.

        Arguments:
          accounts (list) - a list of accounts to report on
          periods (list)  - a list of periods to report on
          attribute       - the attribute to report on
        """
        known_attrs = ['gain', 'additions', 'subtractions', 'net additions']
        assert attribute in known_attrs

        table = Table(len(accounts), len(periods) + 1)
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
                    row.append(Cell(perf[attribute],
                                    fmt="{: ,.2f}", meta=meta))

                except Exception as E:
                    row.append(Cell(None, f=0, s='---'))
                    _log.debug("Empty cell: %s %s %s -> %s", name,
                               act.name, period, E)

            if maxcarry:
                row[0] = act.name + " [c%d]" % (maxcarry)
            table.set_row(i, row)

        f = ['Total:']
        for columni in range(len(periods)):
            f.append(Cell(sum([c for c in table.column(columni + 1)]),
                          fmt='{: ,.2f}'))
        table.set_footer(f)
        table.set_column_formats([CF('<', 30)] + [CF('>', 15)]*len(periods))
        self.table = table


class DetailReport(object):
    """Displays many periods and statistics for a single account.

    Periods are placed in rows, while account statistics (performance, gain,
    etc.) are placed in columns.  This report shows columns containing:
     - start date
     - IRR
     - additions
     - subtractions
     - start balance
     - end balance
     - gain

    Cell metadata:
      None

    Annotations:
     if an account had carried values reported, the account name has a string:
     '[cX]' appended which indicates the longest carry (maximum number of
     days for which the information is out of date).

    """

    def __init__(self, account, periods, name=None):
        """Initialize the Detail Report.

        Arguments:
            account - the account to report on
            periods (list) - a list of periods to examine
            name -   the name of the report
        """
        if not name:
            life = "{:%Y-%m-%d} to {:%Y-%m-%d}".format(account._topen,
                                                       account._values[-1].t)

            name = "{:s} --  Detail Report over the lifetime {:s} ".format(
                account.name, life)

        self.name = name

        table = Table(len(periods), 8)
        header = ["Period", "Start Date", "Performance", "Adds",
                  "Subs", "St. Value", "End Value", "Gain"]
        table.set_header(header)
        for i, period in enumerate(periods):
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
                    row[0] = row[0] + ' [c%d]' % (perf['carry'])
            except Exception as E:
                while len(row) < 8:
                    row.append(Cell(None, f=0, s="---"))
                _log.debug("Empty row: %s %s %s -> %s", name,
                           account.name, period, E)

            table.set_row(i, row)

        table.set_column_formats([CF('<', 18)]*2 + [CF('>', 18)]*6)
        self.table = table
