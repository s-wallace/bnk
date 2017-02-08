import logging
import datetime as dt
from bnk import read_records, read_bnk_data
from bnk import fiscalyear as fy
from bnk import reporting



_log = logging.getLogger('bnk.main')

def main(args):
    """The bnk main method, without option parsing. The following arguments are possible:

    args.carryvalues  (int) - the number of days that a value can be carried forward
    args.report       (str) - a string representing an importable module
    args.carry_last  (bool) - True iff the last value in each open account should be carried to report date
    args.date        (date) - A datetime.date instance representing when the report should be run
    """
    if args.report:
        import importlib
        report = importlib.import_module(args.report)

        for fname in args.files:
            with open(fname, 'r') as fin:
                data = fin.read()
                accounts = read_bnk_data(data)

                for acts in [accounts['Account'], accounts['Meta']]:
                    for actname in acts:
                        acts[actname].carryvalues = dt.timedelta(days=args.carry_forward)
                        if args.carry_last:
                            try:
                                acts[actname].carrylast(args.date)
                            except:
                                pass

        report.report(args, accounts)

if __name__ == "__main__":

    import argparse

    PARSER = argparse.ArgumentParser(description="bnk: account analysis")
    PARSER.add_argument('files', nargs='+', help="records file(s) to load")
    PARSER.add_argument('--date', help="date for report YYYYMMDD (deafult=last quarter)")
    PARSER.add_argument('--carry-forward', type=int, default=0,
                        help="Carry balances forward N days from previous marks if necessary")
    PARSER.add_argument('--carry-last', action='store_true',
                        help="Carry last account balances to current report date if need be.")
    PARSER.add_argument('--report')

    CLARGS = PARSER.parse_args()
    if not CLARGS.date:
        CLARGS.date = fy.end_of_completed_quarter(dt.date.today())

    _log.info("ARGS: %s"%(str(CLARGS)))
    main(CLARGS)
