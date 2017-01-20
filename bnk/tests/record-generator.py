import bnk.fiscalyear as fy
import datetime as dt
import random

class AccountStats(object):
    def __init__(self, name, opening):
        self.name = name
        self.opening = opening
        self.balance = 0
        self.t_liklihood = random.uniform(.3, .7)
        self.i_rate = random.gauss(0, 7)

if __name__ == "__main__":
    import argparse
    _names = ['Abracadabra', 'BoogyTime', 'CatsRUs', 'DogFund', 'Eatin', 'Finkies']
    parser = argparse.ArgumentParser()
    parser.add_argument('--accounts', type=int, default=5)
    parser.add_argument('--timespan', nargs=2, help="timespan of records YYYYMMDD YYYYMMDD")

    args = parser.parse_args()
    start = dt.date(int(args.timespan[0][:4]), int(args.timespan[0][4:6]), int(args.timespan[0][6:8]))
    end = dt.date(int(args.timespan[1][:4]), int(args.timespan[1][4:6]), int(args.timespan[1][6:8]))
    span = (end-start).days

    accounts = []

    for n in range(args.accounts):
        r = random.random()
        if r < .3:
            print("{0:%m-%d-%Y} open {1:s}".format(start, _names[n]))
            accounts.append(AccountStats(_names[n], start))
        else:
            opening = start+dt.timedelta(days=int(r*span/3.0))
            print("{0:%m-%d-%Y} open {1:s}".format(opening, _names[n]))
            accounts.append(AccountStats(_names[n], opening))

    qends = [q for q in fy.quarter_ends(start, end)]
    if qends[0] < start:
        qends.pop(0)
    if qends[-1] > end:
        qends.pop()
    # now, qends are within the range (start, end)
    for q in qends:
        print("")
        has_transaction = False
        for a in accounts:
            if a.opening + dt.timedelta(days=95) >= q: continue

            r = random.random()
            if r < a.t_liklihood:
                r = random.randrange(1,10)
                r *= 1000
                if not has_transaction:
                    print("during %s"%fy.quarter_name(q))
                    print("---")
                    has_transaction = True
                print("Assets -> {0:<20s} {1:>10d}".format(a.name, int(r)))
                a.balance += r
                r = random.uniform(a.i_rate - 4, a.i_rate + 4)
                r /= 400.  # /100 cause percentage /4 cause quarterly
                a.balance *= (1+r)

        print("")
        print("{0:%m-%d-%Y} balances".format(q))
        print("---")
        for a in accounts:
            if a.opening < q:
                print("{0:<30s} {1:>10d}".format(a.name, int(a.balance)))
