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
        sortedmeta = ['%s:%s'%(i[0],i[1]) for i in sorted(self.meta.items())]
        return "Cell(%s, f=%f, s='%s' meta={%s})"%(str(self._obj), self._f, self._s, ','.join(sortedmeta))

class CF(object):
    """Column Format"""
    def __init__(self, justify='>', width=0):
        self.justify = justify
        self.width = width

    def format(self, s):
        fmtstr = '{:'+self.justify+str(self.width)+"s}"
        return fmtstr.format(s)

    def __repr__(self):
        return '{:'+self.justify+str(self.width)+"s}"

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
        if isinstance(value, Table):
            assert value._cols == self._cols
            myrow = value
        else:
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

    def column(self, coli, h=False, f=False, r=False):
        if h and self.has_header():
            yield self._header[coli]
        for row in self._table:
            if isinstance(row, Table):
                if r:
                    for c in row.column(coli, h, f, r):
                        yield c
            else:
                yield row[coli]
        if f and self.has_footer():
            yield self._footer[coli]

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
