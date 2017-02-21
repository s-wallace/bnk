"""Tables hold Cells."""


class Cell(object):
    """A table cell. Holds an object, meta data and string/float views."""

    def __init__(self, obj, f=None, fmt=None, s=None, meta=None):
        """Initialize a Cell.

        Arguments:
         obj - the object to hold
         f   - a floating point representation (default None)
         fmt - a format string to generate a string representation
         s   - a string representation of the object
         meta - a dictionary of metadata
        """
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
        """Return the wrapped object."""
        return self._obj

    def isnumber(self):
        """Return True iff the wapper object is a float or int."""
        return (isinstance(self._obj, float) or isinstance(self._obj, int))

    def __float__(self):
        return self._f

    def __add__(self, other):
        return self._f + float(other)

    def __radd__(self, other):
        return self._f + float(other)

    def stringify(self, fmt=None):
        """(Re)generate the 'string' represenation of the cell.

        Apply the specified fmt string, if given, or use a default
        format.
        """

        if fmt:
            self._s = fmt.format(self._obj)
            return

        if isinstance(self._obj, str):
            self._s = self._obj
        elif isinstance(self._obj, float):
            self._s = "%.2f" % self._obj
        else:
            self._s = str(self._obj)

    def __format__(self, fmt):
        """Format the string representation: adjust width and alignment."""
        if not isinstance(fmt, str):
            raise TypeError("must be str!")
        fmtstr = "{0:" + fmt + "}"
        return fmtstr.format(self._s)

    def __repr__(self):
        srtmeta = ['%s:%s' % (i[0], i[1]) for i in sorted(self.meta.items())]
        return "Cell(%s, f=%f, s='%s' meta={%s})" % (str(self._obj), self._f,
                                                     self._s,
                                                     ','.join(srtmeta))


class CF(object):
    """CF instances represent preferred column width and justification."""

    def __init__(self, justify='>', width=0):
        """Initialize with specified justification and width."""
        self.justify = justify
        self.width = width

    def format(self, s):
        """Return the given string; formatted for width, and justificaion."""
        fmtstr = '{:' + self.justify + str(self.width) + "s}"
        return fmtstr.format(s)

    def __repr__(self):
        return '{:' + self.justify + str(self.width) + "s}"


class Table(object):
    """A Table holds Cell instances."""

    def __init__(self, rows, cols, growable=False):
        """Initialize a table with specified number of rows and columns."""

        self._table = []
        for r in range(rows):
            self._table.append([None] * cols)

        self._footer = None
        self._header = None
        self._rows = rows
        self._cols = cols
        self._growable = growable

    def addrow(self):
        """Add a new row to the table, if possible."""
        if not self._growable:
            return False

        self._rows += 1
        self._table.append([None] * self._cols)
        return True

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
        """Set a row's worth of data."""

        if isinstance(value, Table):
            assert value._cols == self._cols
            myrow = value
        else:
            assert len(value) == self._cols
            myrow = self._check_vector(value)

        self._table[rowi] = myrow

    def set_column(self, coli, value):
        """Set the cells in a column of the table."""
        assert len(value) == self._rows
        mycol = self._check_vector(value)
        for i, row in enumerate(self._table):
            row[coli] = mycol[i]

    def set_cell(self, rowi, colj, value):
        """Set the cell of the table."""
        myv = self._check_vector([value])[0]
        self._table[rowi][colj] = myv

    def row(self, rowi):
        """Generate all cells in the specified row."""
        for item in self._table[rowi]:
            yield item

    def column(self, coli, h=False, f=False, r=False):
        """Generate the cells in a column.

        Arugments:
         h - True to include the column header
         f - True to include the column footer
         r - True to generate entries from nested tables
        """
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
        """Set the table header."""

        assert len(header) == self._cols
        self._header = self._check_vector(header)

    def set_footer(self, footer):
        """Set the table footer."""

        assert len(footer) == self._cols
        self._footer = self._check_vector(footer)

    def has_header(self):
        """True iff the table has a header."""
        return bool(self._header)

    def has_footer(self):
        """True iff the table has a footer."""
        return bool(self._footer)

    def set_column_formats(self, cf):
        """Set the column formats for this table."""
        self._cf = cf

    def cf(self):
        """Return the column formats for this table."""
        return self._cf
