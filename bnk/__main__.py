"""bnk: (simple) financial analysis with incomplete information."""

import logging
import datetime as dt
from bnk import read_bnk_data
from bnk import fiscalyear as fy

_log = logging.getLogger('bnk.main')


def parse_args(arglist=None):
    """Parse arguments (typically from the commandline)."""

    import argparse

    parser = argparse.ArgumentParser(description="bnk: account analysis")
    parser.add_argument('file', help="records file to load")
    parser.add_argument('--date',
                        help="date for report YYYYMMDD (deafult=last quarter)")
    parser.add_argument('--carry-forward', type=int, default=0,
                        help="Carry balances forward N days from previous"
                        " marks if necessary")
    parser.add_argument('--carry-last', action='store_true',
                        help="Carry last account balances to current report"
                        " date if need be.")
    parser.add_argument('--report')

    args = parser.parse_args(arglist)
    if not args.date:
        args.date = fy.end_of_completed_quarter(dt.date.today())
    else:
        args.date = dt.date(int(args.date[:4]),
                            int(args.date[4:6]),
                            int(args.date[6:8]))

    _log.info("ARGS: %s" % (str(args)))
    return args


def main(args):
    """The bnk main method, without option parsing.

    The following arguments are possible:

    args.carryvalues  (int) - the number of days that a value can be
                                carried forward
    args.report       (str) - a string representing an importable module
    args.carry_last  (bool) - True iff the last value in each open account
                                should be carried to report date
    args.date        (date) - A datetime.date instance representing when the
                                report should be run
    """
    if args.report:
        import importlib
        report = importlib.import_module(args.report)

        if args.file:
            with open(args.file, 'r') as fin:
                data = fin.read()
        elif args.data:
            data = args.data
        else:
            raise ValueError("Must specify a file or pass data to read")

        accounts = read_bnk_data(data, carry_last=args.carry_last,
                                 to_date=args.date)

        for acts in [accounts['Account'], accounts['Meta']]:
            for actname in acts:
                carrydays = dt.timedelta(days=args.carry_forward)
                acts[actname].carryvalues = carrydays

        report.report(args, accounts)


if __name__ == "__main__":

    ARGS = parse_args()
    main(ARGS)
