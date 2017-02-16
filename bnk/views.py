import sys
from bnk.tables import Table

class NativeView(object):

    def __init__(self, stream=sys.stdout, buffer=False):
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

    def append(self, report, **args):
        content = _native_view_recursive(report.table, depth=0, **args)
        if self.buffer:
            self._bcontent.append(content)
            self._bcontent.append(self.between_report)
        else:
            print(content, file=self.stream)
            print(self.between_report, file=self.stream)


def native_view(report, **args):
    """Native view: one cell per line showing the cell's full data"""
    return _native_view_recursive(report.table, depth=0, **args)

def _native_view_recursive(table, depth, **args):
    data = []
    if depth == 0 and 'title' in args:
        data.append("Table: %s"%args['title'])

    if table.has_header():
        for i,cell in enumerate(table._header):
            data.append("(Header, {:d}) {!r}".format(i, cell))
    for i, row in enumerate(table._table):
        if isinstance(row, Table):
            data.append("({:d}, *) Begin Nested Table")
            data.extend(self._native_view_recursive(row, depth+1, **args))
            data.append("({:d}, *) End Nested Table")
        else:
            for j, cell in enumerate(row):
                data.append("({:d}, {:d}) {!r}".format(i,j,cell))
    if table.has_footer():
        for i,cell in enumerate(table._footer):
            data.append("(Footer, {:d}) {!r}".format(i,cell))
    return "\n".join(data)

class AsciiView(NativeView):

    def append(self, report, **args):
        content = _ascii_view_recursive(report.table, depth=0, **args)
        if self.buffer:
            self._bcontent.append(content)
            self._bcontent.append(self.between_report)
        else:
            print(content, file=self.stream)
            print(self.between_report)


def ascii_view(report, **args):
    """Avaiable args:
    indent      (int):
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

    return _ascii_view_recursive(report.table, **args)

def _ascii_view_recursive(table, depth=0, c_annotes=None, **args):
    """Internal helper function"""

    if not 'headerstyle' in args: args['headerstyle'] = '=_'
    if not 'footerstyle' in args: args['footerstyle'] = '-\n'
    if not 'bodystyle' in args: args['bodystyle'] = ' >'
    if not 'bannerchar' in args: args['bannerchar'] = '-'
    if not 'title' in args: args['title'] = ""
    if not 'minstr' in args: args['minstr'] = '- '
    if not 'maxstr' in args: args['maxstr'] = '+ '

    banners = []


    known_metadata = {'min', 'max', 'carry'}

    # first pass, look to see if we need space at left and right side
    # of the column
    if c_annotes == None:
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
                        "ascii_view can't handle '%s'"%meta

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

            ftable.append(_ascii_view_recursive(row, depth+1,
                                                c_annotes, **nargs))
            ftable.append([]) # Empty row after a table
            continue

        stringrow = []
        for i, colannote, cell, cfmt in zip(range(len(row)), c_annotes, row, table.cf()):
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
            fmt = '{:'+cfmt.justify+str(cfmt.width)+"s}"
            stringrow.append(fmt.format(stringrep))
        ftable.append(stringrow)

    # now we have all the strings built, note that some of these "lines"
    # are actually entire tables with linebreaks...
    lines = [''.join(c for c in row) for row in fheader+ftable+ffooter]
    # since some lines may in fact be entire tables we need a more complex call
    maxlinelen = max(len(s) for l in lines for s in l.splitlines())
    banner = args['bannerchar']*maxlinelen

    # add banners and extra line breaks
    if table.has_header() and args['headerstyle']:
        if args['headerstyle'].startswith('-'): banners.append(0)
        elif args['headerstyle'].startswith('_'): banners.append(1)
        elif args['headerstyle'].startswith('='): banners.extend([0,1])
        elif args['headerstyle'].startswith('\n'): lines.insert(1, '')

    if table.has_footer() and args['footerstyle']:
        if args['footerstyle'].startswith('-'): banners.append(len(lines)-1)
        elif args['footerstyle'].startswith('_'): banners.append(len(lines))
        elif args['footerstyle'].startswith('='):
            banners.extend([len(lines)-1,len(lines)])
        elif args['footerstyle'].startswith('\n'):
            lines.insert(len(lines)-1, '')

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
