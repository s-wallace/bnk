"""Tests for arguments passed in via command-line usage."""

import datetime as dt
import unittest
from bnk import __main__ as main
from bnk.tests import recstrings


class ArgsTest(unittest.TestCase):
    """Test cases for command line arguments."""

    def test_carrylast_viareport(self):
        """Verify --carry-last impacts at report time."""

        arg_str = '--carry-last --date 20021231 DUMMY_FILE'
        args = main.parse_args(arg_str.split())
        args.data = recstrings.a3t3b3c
        args.report = "bnk.tests.test_args"
        args.file = None  # need to kill this posthoc
        # this argument is used to pass information through the main.main() fn
        # and into the report generation function, where some additional
        # testing occurs
        args.test = "carrylast-true"
        main.main(args)

        # now, without --carry-last, we should see different results
        arg_str = 'DUMMY_FILE'
        args = main.parse_args(arg_str.split())
        args.data = recstrings.a3t3b3c
        args.report = "bnk.tests.test_args"
        args.file = None  # need to kill this posthoc
        # this argument is used to pass information through the main.main() fn
        # and into the report generation function, where some additional
        # testing occurs
        args.test = "carrylast-false"
        main.main(args)


def report(args, accounts):
    """Perform the report-time testing."""

    tests = {'carrylast-true': carrylast_true_test,
             'carrylast-false': carrylast_false_test}

    assert args.test in tests, "Don't know what report-time test to apply!"

    # invoke the test
    tests[args.test](args, accounts)


def carrylast_true_test(args, accounts):
    """Verify that --carrylast impacts meta-account correctly.

    - meta-account name should reflect carrylast status
    - carrylast should impact the Marked status when a record is missing.
    """
    assert args.test == "carrylast-true", "Something went wrong..."

    v = accounts['Meta']['ab'].get_value(dt.date(2002, 12, 31))
    assert accounts['Meta']['ab'].name == 'ab [cl92]', \
        "Carrylast didn't set meta-account name"
    assert v == (490.0, 'Marked'), \
        "Carrylast didn't work as expected with meta-account"


def carrylast_false_test(args, accounts):
    """Verify that meta-account performs as expected w/o carrylast."""

    assert args.test == "carrylast-false", "Something went wrong..."

    v = accounts['Meta']['ab'].get_value(dt.date(2002, 12, 31))
    assert accounts['Meta']['ab'].name == 'ab', \
        "Meta account name is unexpected"
    assert v[1] == 'No Data', \
        "Expect NoData unless --carry-last is used."
