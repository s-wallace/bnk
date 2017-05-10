"""Test parsing of record string data."""

import datetime as dt
import unittest
from bnk.parse import read_bnk_data, last_error_token


class ParsingTest(unittest.TestCase):
    """Test cases parsing record strings."""

    def test_valid_parsing(self):
        """Test all syntax recognized by parser."""

        minrecs = """
           12-30-2001 open a
           12-30-2001 open b
           01-01-1900 open Assets
           10-01-2000 open closeon10102000
        """
        bd = read_bnk_data(minrecs)
        self.assertEqual(bd['Account']['a']._topen, dt.date(2001, 12, 30))
        self.assertEqual(bd['Account']['b']._topen, dt.date(2001, 12, 30))
        self.assertEqual(bd['Account']['closeon10102000']._topen,
                         dt.date(2000, 10, 1))
        self.assertEqual(bd['Account']['Assets']._topen,
                         dt.date(1900, 1, 1))

        minrecs = minrecs + """
          10-10-2000 close closeon10102000
        """
        bd = read_bnk_data(minrecs)
        self.assertEqual(bd['Account']['closeon10102000']._tclose,
                         dt.date(2000, 10, 10))

        minrecs = minrecs + """
           from 12-31-2001 until 12-31-2001
           ---
           Assets -> a   200
           Assets -> b   200
           a -> b        -50
           """
        bd = read_bnk_data(minrecs)

        minrecs = minrecs + """
           12-31-2001 balances
           ---
           a      250
           b      150
           Assets 1000
        """
        bd = read_bnk_data(minrecs)

        minrecs = minrecs + """
           // comment

           01-31-2001 balances
           ---
           Assets 1000  // comment
        """
        bd = read_bnk_data(minrecs)

    def test_invalid_parsing(self):
        """Test parsing error detection."""

        valid = """
           12-30-2001 open a
           12-30-2001 open b
           01-01-1900 open Assets
           10-01-2000 open closeon10102000
        """

        invalid = valid + """
           10-20-20  open c     // dates must be mm-dd-yyyy
        """
        self.assertRaises(SyntaxError, read_bnk_data, invalid)
        self.assertEqual(last_error_token().lexer.lineno,
                         len(invalid.splitlines()) - 2)

        invalid = valid + """
           from 12-31-2001 until 12-31-2001
           ---
           a -> xssets   200    // can't use a non-opened account
        """
        self.assertRaises(LookupError, read_bnk_data, invalid, strict=True)
        self.assertEqual(last_error_token().lexer.lineno,
                         len(invalid.splitlines()) - 1)


def print_text_with_linenos(text):
    """Print a block of text with line numbers preceeding each line."""

    print("")
    for i, l in enumerate(text.splitlines()):
        print("%d: %s" % (i, l))
    print("")
