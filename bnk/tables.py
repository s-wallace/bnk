class Cell(object):
    """A table cell. Holds an object, meta data and string/float views"""

    def __init__(self, obj, f=None, fmt=None, s=None):
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

        self.meta = ""

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

    def set_row(self, rowi, value):
        assert len(value) == self._cols
        self._table[rowi] = value

    def set_column(self, coli, value):
        assert len(value) == self._rows
        for i, row in enumerate(self._table):
            row[coli] = value[i]

    def set_cell(self, rowi, colj, value):
        self._table[rowi][colj] = value

    def row(self, rowi):
        for item in self._table[rowi]:
            yield item

    def column(self, coli):
        for row in self._table:
            yield row[coli]

    def set_header(self, header):
        assert len(header) == self._cols
        self._header = header

    def set_footer(self, footer):
        assert len(footer) == self._cols
        self._footer = footer

    def has_header(self):
        return bool(self._header)

    def has_footer(self):
        return bool(self._footer)

    def content(self):
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


def flatten_table(table, **args):
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

    content = table.content()
    lines = [' '*args['indent'] + ''.join(c for c in row) for row in content]
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
