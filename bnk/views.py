"""View classes to transform reports/tables into readable form."""

import sys
from bnk.tables import Table


class NativeView(object):
    """A simple view of a table, mainly useful for debugging and diffing.

    The table is transformed into strings, one cell per line with the cell
    location displayed along with the cell repr string.
    """

    def __init__(self, stream=sys.stdout, buffer=False):
        """Initialize a NativeView.

        Arguments:
          stream - the print stream to receive output (default: sys.stdout)
          buffer - True iff output should be buffered until the instance's
             __exit__() method is called (default: False)
        """
        self.buffer = buffer
        self._bcontent = []
        self.stream = stream
        self.between_report = "\n\n"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.buffer:
            print("\n".join(self._bcontent), file=self.stream)
            self._bcontent = []

    def section(self, name):
        """Create a new 'section' for the report."""

        banner = '-' * (40 - len(name) // 2)
        if self.buffer:
            self._bcontent.append("%s %s %s" % (banner, name, banner))
        else:
            print("%s %s %s" % (banner, name, banner), file=self.stream)

    def append(self, report, **args):
        """Append a report/table to the NativeView.

        Keyword Arguments:
          title (str) -- the title of the report being added.
        """

        content = _native_view_recursive(report.table, depth=0, **args)
        if self.buffer:
            self._bcontent.append(content)
            self._bcontent.append(self.between_report)
        else:
            print(content, file=self.stream)
            print(self.between_report, file=self.stream)


def _native_view_recursive(table, depth, **args):
    data = []
    if depth == 0 and 'title' in args:
        data.append("Table: %s" % args['title'])

    if table.has_header():
        for i, cell in enumerate(table._header):
            data.append("(Header, {:d}) {!r}".format(i, cell))
    for i, row in enumerate(table._table):
        if isinstance(row, Table):
            data.append("({:d}, *) Begin Nested Table")
            data.extend(_native_view_recursive(row, depth + 1, **args))
            data.append("({:d}, *) End Nested Table")
        else:
            for j, cell in enumerate(row):
                data.append("({:d}, {:d}) {!r}".format(i, j, cell))
    if table.has_footer():
        for i, cell in enumerate(table._footer):
            data.append("(Footer, {:d}) {!r}".format(i, cell))
    return "\n".join(data)


class AsciiView(NativeView):
    """A text view of a report/table, useful for display via the terminal.

    The table is transformed into strings and tabular format is maintained.
    Style cues from the report are used to produce the displayed text.
    """

    def append(self, report, **args):
        r"""Append a report to the AsciiView.

        Keyword Arguments:
          bannerchar  : 1-char str
          title       : str
          headerstyle : one char per nested level of table, see formats below
          footerstyle : one char per nested level of table, see formats below
          bodystyle   : one char per nested level of table, see formats below

        header/footer styles:
          '0' : supress header/footer
          '=' : border above and below
          '-' : border above
          '_' : border below
          '\n': blank line before footer or after header

        body styles:
          ' ' : normal
          '>' : body first column indent slightly
        """
        content = _ascii_view_recursive(report.table, depth=0, **args)
        if self.buffer:
            self._bcontent.append(content)
            self._bcontent.append(self.between_report)
        else:
            print(content, file=self.stream)
            print(self.between_report)


def _ascii_view_recursive(table, depth=0, c_annotes=None, **args):
    r"""Internal helper method for AsciiView.

    Avaiable args:
      bannerchar  (1-char string):
      title       (string)
      headerstyle : one char per nested level of table, see formats below
      footerstyle : one char per nested level of table, see formats below
      bodystyle : one char per nested level of table, see formats below

    header/footer styles:
      '0' : supress header/footer
      '=' : border above and below
      '-' : border above
      '_' : border below
      '\n': blank line before footer or after header

    body styles:
      ' ' : normal
      '>' : body first column indent slightly
    """
    if 'headerstyle' not in args:
        args['headerstyle'] = '=_'
    if 'footerstyle' not in args:
        args['footerstyle'] = '-\n'
    if 'bodystyle' not in args:
        args['bodystyle'] = ' >'
    if 'bannerchar' not in args:
        args['bannerchar'] = '-'
    if 'title' not in args:
        args['title'] = ""
    if 'minstr' not in args:
        args['minstr'] = '- '
    if 'maxstr' not in args:
        args['maxstr'] = '+ '

    banners = []

    known_metadata = {'min', 'max', 'carry'}

    # first pass, look to see if we need space at left and right side
    # of the column
    if c_annotes is None:
        c_annotes = []
        for col in range(table._cols):
            lside = False
            rside = False
            for cell in table.column(col, True, True, True):
                if 'min' in cell.meta or 'max' in cell.meta:
                    lside = True
                if 'carry' in cell.meta:
                    rside = True
                for meta in cell.meta:
                    assert meta in known_metadata, \
                        "ascii_view can't handle '%s'" % meta

            c_annotes.append((lside, rside))

    # build header/footer strings
    fheader = []
    ffooter = []
    if table.has_header() and not args['headerstyle'].startswith('0'):
        # format the cell's string adding space at the end if necessary
        fheader = [[hfmt.format(hcell._s + (' ' if colannote[1] else ''))
                    for hcell, hfmt, colannote in
                    zip(table._header, table.cf(), c_annotes)]]
    if table.has_footer() and not args['footerstyle'].startswith('0'):
        ffooter = [[ffmt.format(fcell._s + (' ' if colannote[1] else ''))
                    for fcell, ffmt, colannote in
                    zip(table._footer, table.cf(), c_annotes)]]

    # build strings for the body...
    ftable = []
    for row in table._table:
        if isinstance(row, Table):
            nargs = dict(args)
            nargs['headerstyle'] = nargs['headerstyle'][1:]
            nargs['footerstyle'] = nargs['footerstyle'][1:]
            nargs['bodystyle'] = nargs['bodystyle'][1:]

            ftable.append(_ascii_view_recursive(row, depth + 1,
                                                c_annotes, **nargs))
            ftable.append([])   # Empty row after a table
            continue

        stringrow = []
        for i, colannote, cell, cfmt in zip(range(len(row)),
                                            c_annotes, row, table.cf()):
            stringrep = cell._s
            if colannote[0]:
                if 'min' in cell.meta:
                    stringrep = args['minstr'] + stringrep
                if 'max' in cell.meta:
                    stringrep = args['maxstr'] + stringrep
            if colannote[1]:
                if 'carry' in cell.meta:
                    stringrep = stringrep + "'"
                else:
                    stringrep = stringrep + " "
            if i == 0 and args['bodystyle'] == '>':
                stringrep = ' ' + stringrep
            fmt = '{:' + cfmt.justify + str(cfmt.width) + "s}"
            stringrow.append(fmt.format(stringrep))
        ftable.append(stringrow)

    # now we have all the strings built, note that some of these "lines"
    # are actually entire tables with linebreaks...
    lines = [''.join(c for c in row) for row in fheader + ftable + ffooter]
    # since some lines may in fact be entire tables,
    # we need a more complex call
    maxlinelen = max(len(s) for l in lines for s in l.splitlines())
    banner = args['bannerchar'] * maxlinelen

    # add banners and extra line breaks
    if table.has_header() and args['headerstyle']:
        if args['headerstyle'].startswith('-'):
            banners.append(0)
        elif args['headerstyle'].startswith('_'):
            banners.append(1)
        elif args['headerstyle'].startswith('='):
            banners.extend([0, 1])
        elif args['headerstyle'].startswith('\n'):
            lines.insert(1, '')

    if table.has_footer() and args['footerstyle']:
        if args['footerstyle'].startswith('-'):
            banners.append(len(lines) - 1)
        elif args['footerstyle'].startswith('_'):
            banners.append(len(lines))
        elif args['footerstyle'].startswith('='):
            banners.extend([len(lines) - 1, len(lines)])
        elif args['footerstyle'].startswith('\n'):
            lines.insert(len(lines) - 1, '')

    if banners:
        banners.sort()
        # from back to front
        while banners:
            bloc = banners.pop()
            lines.insert(bloc, banner)
    if depth == 0 and args['title']:
        lines.insert(0, args['title'])

    # build the string
    return '\n'.join(lines)
