class Cell(object):
    """A table cell. Holds an object, meta data and string/float views"""

    def __init__(self, obj, f=None, fmt=None, s=None, meta=None):
        self._obj = obj
        if f is None:
            try:
                self._f = float(obj)
            except:
                self._f = float('nan')
        else:
            self._f = f

        if s:
            self._s = s
        else:
            self.stringify(fmt)

        if meta is None:
            self.meta = {}
        else:
            self.meta = meta

    def object(self):
        return self._obj

    def isnumber(self):
        return (isinstance(self._obj, float) or isinstance(self._obj, int))

    def __float__(self):
        return self._f

    def __add__(self, other):
        return self._f + float(other)

    def __radd__(self, other):
        return self._f + float(other)

    def restring(self, funct):
        """Regenerate the 'string' represenation of the cell by calling
        the specified function with the cell itself as an argument"""
        self._s = funct(self)

    def stringify(self, fmt=None):
        """Regenerate the 'string' represenation of the cell
        by formatting the underlying object using a default
        format if necessary"""

        if fmt:
            self._s = fmt.format(self._obj)
            return

        if isinstance(self._obj, str):
            self._s = self._obj
        elif isinstance(self._obj, float):
            self._s = "%.2f"%self._obj
        else:
            self._s = str(self._obj)

    def __format__(self, fmt):
        """Format the string representation, i.e., adjust width and alignment"""
        if not isinstance(fmt, str):
            raise TypeError("must be str!")
        fmtstr = "{0:"+fmt+"}"
        return fmtstr.format(self._s)

    def __repr__(self):
        return "Cell(%s, f=%f, s=%s)"%(str(self._obj), self._f, self._s)

class CF(object):
    """Column Format"""
    def __init__(self, justify='>', width=0):
        self.justify = justify
        self.width = width

    def stringify(self, s):
        fmtstr = '{:'+self.justify+str(self.width)+"s}"
        return fmtstr.format(s)


class Table(object):
    """A Table holds cells"""

    def __init__(self, rows, cols):
        self._table = []
        for r in range(rows):
            self._table.append([None]*cols)


        self._footer = None
        self._header = None
        self._rows = rows
        self._cols = cols

    def restring(self, cfmts=None):
        """Restring the table's columns using the specified function on
        the corresponding column. If 'None' is passed in lieu of a
        function, restring is not called on that column's cells"""

        if cfmts:
            for i in range(self._cols):
                for cell in self.column(i):
                    if cfmts[i]:
                        cell.restring(cfmts[i])

    def _check_vector(self, value):
        myv = []
        for c in value:
            if isinstance(c, str):
                myv.append(Cell(c))
            elif isinstance(c, Cell):
                myv.append(c)
            else:
                raise ValueError("Table elements must be str or Cell")
        return myv

    def set_row(self, rowi, value):
        assert len(value) == self._cols
        myrow = self._check_vector(value)
        self._table[rowi] = myrow

    def set_column(self, coli, value):
        assert len(value) == self._rows
        mycol = self._check_vector(value)
        for i, row in enumerate(self._table):
            row[coli] = mycol[i]

    def set_cell(self, rowi, colj, value):
        myv = _check_vector([value])[0]
        self._table[rowi][colj] = myv

    def row(self, rowi):
        for item in self._table[rowi]:
            yield item

    def column(self, coli):
        for row in self._table:
            yield row[coli]

    def set_header(self, header):
        assert len(header) == self._cols
        self._header = self._check_vector(header)

    def set_footer(self, footer):
        assert len(footer) == self._cols
        self._footer = self._check_vector(footer)

    def has_header(self):
        return bool(self._header)

    def has_footer(self):
        return bool(self._footer)

    def set_column_formats(self, cf):
        self._cf = cf

    def cf(self):
        return self._cf

    def xcontent(self):
        t = []
        if self._header:
            t.append(self._header)

        for row in self._table:
            t.append(row[:])

        if self._footer:
            t.append(self._footer)
        return t

class StringView(object):
    def __init__(self, table, cfmts, hfmts=None):
        self._columnformats = cfmts
        self._headerformats = hfmts
        self._table = table

    def content(self):
        content = self._table.content()

        header = ""
        if self._headerformats:
            headerrow = content.pop(0)
            header = [h.format(hcell) for hcell, h in zip(headerrow, self._headerformats)]
            table = [header] + [[c.format(cell) for cell, c in zip(row, self._columnformats)]
                                for row in content]
        else:
            table = [[c.format(cell) for cell, c in zip(row, self._columnformats)]
                     for row in content]

        return table


def ascii_view(report, **args):
    """Avaiable args:
    indent      (int):
    bannerchar  (1-char string):
    title       (string)
    headerstyle
    """
    if not 'banners' in args: args['banners'] = []
    if not 'indent' in args: args['indent'] = 0
    if not 'headerstyle' in args: args['headerstyle'] = '='
    if not 'footerstyle' in args: args['footerstyle'] = '-'
    if not 'bannerchar' in args: args['bannerchar'] = '-'
    if not 'title' in args: args['title'] = ""

    table = report.table
    if table.has_header():
        headerrow = table._header
        fheader = [[h.stringify(hcell._s) for hcell, h in zip(headerrow, table.cf())]]
    else:
        fheader = []
    if table.has_footer():
        footerrow = table._footer
        ffooter = [[f.stringify(fcell._s) for fcell, f, in zip(footerrow, table.cf())]]
    else:
        ffooter = []

    known_metadata = {'min', 'max', 'carry'}

    # first pass, look to see if we need space at left and right side
    colannotations = []
    for coli in range(table._cols):
        lside = False
        rside = False
        for cell in table.column(coli):
            if 'min' in cell.meta or 'max' in cell.meta:
                lside = True
            if 'carry' in cell.meta:
                rside = True
            for meta in cell.meta:
                assert meta in known_metadata, \
                    "ascii_view can't handle '%s'"%meta

        colannotations.append((lside, rside))

    # second pass, build strings
    ftable = []
    for row in table._table:
        stringrow = []
        for cann, cell, c in zip(colannotations, row, table.cf()):
            stringrep = cell._s
            if cann[0]:
                if 'min' in cell.meta:
                    stringrep = "v " + stringrep
                if 'max' in cell.meta:
                    stringrep = "^ " + stringrep
            if cann[1]:
                if 'carry' in cell.meta:
                    stringrep = stringrep + "'"
                else:
                    stringrep = stringrep + " "
            fmt = '{:'+c.justify+str(c.width)+"s}"
            stringrow.append(fmt.format(stringrep))
        ftable.append(stringrow)

    lines = [' '*args['indent'] + ''.join(c for c in row) for row in fheader+ftable+ffooter]
    maxlinelen = max(len(l) for l in lines)
    banner = args['bannerchar']*maxlinelen

    if table.has_header() and args['headerstyle']:
        if args['headerstyle'] == '-': args['banners'].append(0)
        elif args['headerstyle'] == '_': args['banners'].append(1)
        elif args['headerstyle'] == '=': args['banners'].extend([0,1])

    if table.has_footer() and args['footerstyle']:
        if args['footerstyle'] == '-': args['banners'].append(len(lines)-1)
        elif args['footerstyle'] == '_': args['banners'].append(len(lines))
        elif args['footerstyle'] == '=':
            args['banners'].extend([len(lines)-1,len(lines)])

    if args['banners']:
        args['banners'].sort()
        # from back to front
        while args['banners']:
            bloc = args['banners'].pop()
            lines.insert(bloc, banner)
    if args['title']:
        lines.insert(0, args['title'])

    return '\n'.join(lines)
