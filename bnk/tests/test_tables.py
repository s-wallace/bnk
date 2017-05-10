"""Tests for the bnk.tables module."""

import unittest
from bnk import tables


class TableTest(unittest.TestCase):
    """Test cases for the bnk.tables module."""

    def test_cell(self):
        """Test Cell instances for basic functionality."""
        c = tables.Cell(10.0)

        self.assertEqual(float(c), 10.0)
        self.assertEqual(c._s, "10.00")
        self.assertEqual(c.object(), 10.0)
