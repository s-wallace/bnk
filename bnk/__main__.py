from bnk import read_records
from bnk import fiscalyear as fy
from bnk import reporting

def main(args):
    if args.report:
        import importlib
        report = importlib.import_module(args.report)

        for fname in args.files:
            with open(fname, 'r') as fin:
                data = fin.read()
                accounts = read_records(data)
                for actname in accounts:
                    accounts[actname].carryvalues = args.carry_forward

        report.report(args, accounts)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="bnk: account analysis")
    parser.add_argument('files', nargs='+', help="records file(s) to load")
    parser.add_argument('--date', help="date for report YYYYMMDD (deafult=last quarter)")
    parser.add_argument('--carry-forward', type=int, default=0,
                        help="Carry balances forward N days from previous marks if necessary")
    parser.add_argument('--report')

    args = parser.parse_args()
    print("ARGS:", args)
    main(args)
