"""
Financial reports with incomplete information
"""

import logging
import operator
import datetime as dt
import bisect
import logging
import collections
import csv
from decimal import Decimal

_log = logging.getLogger(__name__)

class Account(object):
    """An Account is a black box with transactions and point values.

    It has the following properties:
      1. It has an opening date, topen. At any point
         t <= topen, the balance is 0.
      2. It has a closing date, tclose. At any point
         t >= tclose, the balance is 0.
      3. You can add money to it (at time topen<=t<=tclose)
      4. You can take money out of it (at time topen<=t<=tclose)
      5. It has a value at any point between topen and tclose

    An account treats the balance as a value at a specific
    point in time.

    Transactions, however, occur within a window of time, and
    not at a specific point (although the window may be
    arbitrarily small).

    An account stores transactions and value 'measurements' or
    'marks'. These are ordered in time as follows:

     - all transactions and marks must occur > topen and <= tclose
     - transactions have a start and end window such that they actually
         occur at a time >= start and <= end (inclusive of their endpoints)
     - for transactions start/end times all occur "before" marks with
         equivilant times
     - transaction windows can't span a mark (thus it is illegal for a
         transaction window to have the same start date as a mark unless
         the transaction window's end date is the same its start)

    An account is intended to support the following types of
    queries:
    1. what is the value at time t
    2. what are the net additions/subtractions between
       time ti and tj (this will be an envelope).
    3. what is the average annual rate of return for
       a given period
    """

    def __init__(self, name, topen):
        """Creates a new account, with the specified opening date."""

        self.name = name

        if topen <= dt.date.min:
            raise ValueError((
                "{0}: Opening date must be after {1:%Y-%m-%d}"
                ).format(self.name, dt.date.min))

        self._topen = topen
        self._tclose = None

        self._transactions = []
        self._values = [Value(topen, 0.0)]

        # allow balances from a previously marked date
        # to be carried forward into the future (specified in days)
        self.carryvalues = None
        self._cl = False

    def to_csv(self, stream):
        """Export to csv"""

        items = []
        items.extend(self._transactions)
        items.extend(self._values)
        items.sort(key=operator.itemgetter(0))
        csvw = csv.writer(stream)

        longmoney = self._values[:]
        shortmoney = self._values[:]
        for i in self._transactions:
            if i.amount >= 0:
                longmoney.append((i.tstart, i.amount))
                shortmoney.append((i.tend, i.amount))
            else:
                longmoney.append((i.tend, i.amount))
                shortmoney.append((i.tstart, i.amount))
        longmoney.sort(key=operator.itemgetter(0))
        shortmoney.sort(key=operator.itemgetter(0))
        assert len(longmoney) == len(shortmoney)
        assert len(longmoney) == len(items)

        tfmt = "{0:%m/%d/%Y}"
        for (n, i) in enumerate(items):
            if isinstance(i, Value):
                r = [tfmt.format(i.t), tfmt.format(i.t), i.value, None]
            elif isinstance(i, Transaction):
                r = [tfmt.format(i.tstart), tfmt.format(i.tend), None, i.amount]
            else:
                raise ValueError("Unexpected thing!")
            lmi = longmoney[n]
            if isinstance(lmi, Value):
                r.extend([tfmt.format(lmi.t), lmi.value, 0])
            else:
                r.extend([tfmt.format(lmi[0]), None, lmi[1]])
            smi = shortmoney[n]
            if isinstance(smi, Value):
                r.extend([tfmt.format(smi.t), smi.value, 0])
            else:
                r.extend([tfmt.format(smi[0]), None, smi[1]])

            csvw.writerow(r)

    def is_open(self, t):
        """True iff the account is open at time t"""

        if t < self._topen:
            return False
        # by 'open' I mean that there may be transactions, so
        # so, we want > _tclose since there could be transactions
        # prior to the 0 balance at _tclose
        if self._tclose and t > self._tclose:
            return False
        return True

    def _check_time(self, t):
        """Ensure a time window t=(t_start, t_end) is valid in that:

        1. t_start <= t_end
        2. t_start > opening date
        3. t_end <= closing date
        """

        ts, tf = t
        if tf < ts:
            raise ValueError(
                "End of time window must be at or after the start")

        if ts <= self._topen:
            raise ValueError((
                "{0}: Can't perform Account operations "
                "at or prior to opening {1:%Y-%m-%d}"
                ).format(self.name, self._topen))


        if self._tclose != None and tf > self._tclose:
            raise ValueError((
                "{0}: Can't perform Account operations "
                "after closing {1:%Y-%m-%d}"
                ).format(self.name, self._tclose))


    def add_transaction(self, trans):
        """Add a transactions to the account"""

        self._check_time((trans.tstart, trans.tend))

        # validate this tx....
        for val in self._values:
            if val.t >= trans.tstart and val.t < trans.tend:
                raise ValueError("Transaction overlaps known Value")

        self._transactions.append(trans)

    def mark_value(self, value):
        """Mark the account's value at a specific moment in time"""

        if value.t == self._topen and value.value == 0.0:
            _log.warning("Account marks a 0.0 balance on opening date. This is depreciated")
            return

        if value.t == self._tclose and value.value == 0.0:
            _log.warning("Account marks a 0.0 balance on closing date. This is depreciated")
            return

        self._check_time((value.t, value.t))

        # Can't mark a value at _tclose
        if self._tclose and value.t == self._tclose:
            raise ValueError("Can't mark a value at close except via set_closing")


        # validate this valuation....
        for trn in self._transactions:
            if value.t >= trn.tstart and value.t < trn.tend:
                raise ValueError("Value occurs during transaction window")

        # find insertion point to the right of/after existing
        # values of 'entry'
        insertion_pt = bisect.bisect(self._values, value)

        # check that the value immediately to the left
        # does not have the same time...
        if insertion_pt > 0:
            val = self._values[insertion_pt - 1]
            if value.t == val.t:
                if val.value == value.value:
                    return  # nothing to do...
                else:
                    # only allow 1 duplicate (insertion_pt == 1)
                    # for the opening date...
                    raise ValueError((
                        "{0}: {1:%Y-%m-%d} has already "
                        "been valued at {2}"
                        ).format(self.name, val.t, val.value))

        self._values.insert(insertion_pt, value)


    def set_closing(self, t):
        """Set the account's closing date.

        On (and after) the closing date, the account balance is zero
        """

        if self._tclose:
            raise ValueError("You can't close an account twice")

        if t <= self._topen:
            raise ValueError((
                "{0}: Closing date "
                "must be after opening: {1:%Y-%m-%d}"
                ).format(self.name, self._topen))

        # tranasction = ((t_start, t_end), amount)
        # BUG/ASSUMPTION: assumes that transaction windows aren't overlapping
        # otherwise, we can't assume that the last transaction has the last end
        # point
        for trn in self._transactions:
            if t < trn.tend:
                raise ValueError(
                    "Can't close an account before the last transaction %s"%repr(trn))

        if self._values[-1].t > t:
            raise ValueError(
                "Can't close an account prior to the last value mark")
        if self._values[-1].t == t:
            if self._values[-1].value != 0.0:
                raise ValueError(
                    "Can't close an account at a mark != 0.0")
            else:
                # 0.0 is already marked, just set the close time
                self._tclose = t
        else:
            self._values.append(Value(t, 0.0))
            self._tclose = t

    def carrylast(self, todate):
        """Create a 'false' value mark at the specified date if necessary"""

        v = self.get_value(todate)
        if v[1] == 'No Data' or v[1] == 'Carried':
            lastvalue = self._values[-1]
            if todate < lastvalue.t:
                raise ValueError("Can't carry to specified date, it occurs before the last mark")
            self._values.append(Value(todate, lastvalue.value))
            self.name = self.name + " [cl%d]" %(todate - lastvalue.t).days
            self._cl = (todate - lastvalue.t).days

    def get_value(self, t):
        """Determine the account value at time t

        Return a tuple (v,info) such that:
        v is a numeric value
        info is a informative string
        """
        if t < self._topen:
            return (0.0, "Not Open")
        if self._tclose and t > self._tclose:
            return (0.0, "Closed")

        for r in self._values:
            if r.t == t:
                return (r.value, "Marked")

        if self.carryvalues:
            for r in reversed(self._values):
                if r.t <= t and t-r.t < self.carryvalues:
                    return (r.value, 'Carried', t-r.t)

        return (float('nan'), "No Data")


    def get_performance(self, start, end, keys):
        """Get various performance measures over a specified period

        Arguments:
         start -- the starting date/time of the period
         end   -- the ending date/time of the period
         keys  -- a dict that will hold performance key/values

         start and end must correspond to value 'marks' in the account.

        Returns:
         True if no errors occur
        """
        if start is None:
            start = self._topen
        if end is None:
            end = self._values[-1].t

        startvalue = self.get_value(start)
        endvalue = self.get_value(end)

        if startvalue[1] != 'Marked' and startvalue[1] != 'Carried':
            raise ValueError("? startval", startvalue)
        if endvalue[1] != 'Marked' and endvalue[1] != 'Carried':
            raise ValueError("? endvalue", endvalue)


        carrylength = 0
        if startvalue[1] == 'Carried':
            carrylength = max(carrylength, startvalue[2].days)
        if endvalue[1] == 'Carried':
            carrylength = max(carrylength, endvalue[2].days)

        keys['carry'] = carrylength
        #start, end, starti, endi = self.get_value_indices(start, end)
        keys['start date'] = start
        keys['end date'] = end

        # If there is a value marked at the start and end
        # time, we also know that no transactions cross
        # those boundaries.  Thus, this check should be redundant
        # (except if carrys happen)
        for trn in self._transactions:
            if trn.tstart <= start and trn.tend > start:
                raise ValueError('Transaction spans start date (carry?)')
            # strictly > here since transactions are computed before values
            if trn.tend > end and trn.tstart <= end:
                raise ValueError('Transaction spans end date (carry?)')

        keys['start balance'] = startvalue[0] #self._values[starti].value
        keys['end balance'] = endvalue[0] #self._values[endi].value

        keys['additions'] = 0
        keys['subtractions'] = 0

        # walk the transactions:
        for t in self._transactions:
            if t.tstart > start and t.tend <= end:
                if t.amount > 0.0:
                    keys['additions'] += t.amount
                else:
                    keys['subtractions'] -= t.amount

        keys['net additions'] = keys['additions'] - keys['subtractions']
        keys['gain'] = (endvalue[0] - startvalue[0] - #self._values[endi].value - self._values[starti].value -
                        keys['additions'] + keys['subtractions'])

        keys['irr'] = self.get_irr(start, end)
        return True

    def get_irr(self, start, end):
        """Implicity calculate the interest earnings (loss) during
        a specific period of time.

        Since all transactions are known, we simply identify the value
        at the start and end of the period and attribute any difference
        in the values to either (1) interest, or (2) transactions.

        However, since transactions occur during a time window (not necessarily
        at a single point in time), we need to consider the impacts of
        differeint transaction timings on the interest calculation.

        There are two scenarios of interest:
         long money timing - money is "in the account" as long as possible
         short money timing - money is "in the account" as little as possible

         in the LMT, money is deposited at the start of a window, but
         withdrawn at the end of a window

         in the SMT, money is withdrawn at the start of a window and
         deposited at the end.

        Return an envelope of possible interest earnings (loss) that account
        for the range of possible transaction timings given each transaction's
        window"""

        if start is None:
            start = self._topen
        if end is None:
            end = self._values[-1].t

        startvalue = self.get_value(start)
        endvalue = self.get_value(end)

        if startvalue[1] != 'Marked' and startvalue[1] != 'Carried':
            raise ValueError("? startval", startvalue)
        if endvalue[1] != 'Marked' and endvalue[1] != 'Carried':
            raise ValueError("? endvalue", endvalue)

        days = (end - start).days

        longmoney_timing = [(days, startvalue[0])]
        shortmoney_timing = [(days, startvalue[0])]


        for t in self._transactions:

            if t.tstart > start and t.tstart <= end:
                assert t.tend <= end, \
                    "Hm.. this seems to imply a transaction crosses a value mark"

                # longmoney: deposits at start of window, withdrawls at end
                # shortmoney: deposits at end of window, withdrawls at start
                if t.is_deposit():
                    longmoney_timing.append(
                        ((end - t.tstart).days, t.amount))
                    shortmoney_timing.append(
                        ((end - t.tend).days, t.amount))
                else:
                    longmoney_timing.append(
                        ((end - t.tend).days, t.amount))
                    shortmoney_timing.append(
                        ((end - t.tstart).days, t.amount))


        rates = []
        for (_, timing) in [('Long', longmoney_timing),
                            ('Short', shortmoney_timing)]:
            precision = 0.00001  # in dollars
            # binary search
            top = 50
            bot = -50
            # shortmoney timing achieves the highest positive interest rate
            assert sum(Decimal(d[1]) * Decimal(1.0+top/100.0)**Decimal(d[0])
                       for d in shortmoney_timing)

            while top - bot > 0:

                rate = bot + (top - bot) / 2.0
                result = 0 + \
                    sum(Decimal(d[1]) * Decimal(1.0+rate/100.0)**Decimal(d[0]) for d in timing)

                if abs(result - Decimal(endvalue[0])) < precision:
                    rates.append(rate)
                    break
                elif result < endvalue[0]:
                    bot = rate
                else:
                    top = rate
            else:
                raise Exception("This shouldn't happen. bot:%f top:%f"%(bot, top))

        rates = [float(((Decimal(1.0+r/100.0)**Decimal(365))-Decimal(1.0))*Decimal(100.0))
                 for r in rates]
        return Range(min(rates), max(rates))


class Value(collections.namedtuple('_V', "t value")):
    """An account valuation (at a moment in time)"""

    def replicate(self, newdate):
        """Return new instance with same value, new date"""

        return Value(newdate, self.value)

    def add_to_account(self, account):
        """Mark specified account with this Value instance"""

        return account.mark_value(self)

    def __cmp__(self, other):
        r = (self.t - other.t).days
        if r != 0:
            return r
        return self.value - other.value

    def __str__(self):
        return "%s: %.2f" % (str(self.t), self.value)


class Transaction(collections.namedtuple('_T', "tstart tend amount")):
    """A Transaction, representing the movement of money during a period"""

    def is_deposit(self):
        """Positive amounts indicate a deposit, negative a withdrawl"""
        return self.amount > 0

    def add_to_account(self, account):
        """Adds this transaction to the specified account"""
        return account.add_transaction(self)

    def __str__(self):
        return "from {0:%m-%d-%Y} until {1:%m-%d-%Y}: {2:.2f}".format(
            self.tstart, self.tend, self.amount)

class Period(collections.namedtuple('_P', 'start end name')):
    def __format__(self, fmt):
        if not isinstance(fmt, str):
            raise TypeError("must be str!")

        return self.name

class Range(collections.namedtuple('_R', 'min max')):
    def __format__(self, fmt):
        if not isinstance(fmt, str):
            raise TypeError("must be str!")
        fmtstr = "({0:"+fmt+"},{1:"+fmt+"})"
        return fmtstr.format(self.min, self.max)


class NoValueAtStartDate(Exception):
    """Indicates that the start of a period does not align with a value mark"""
    pass

class NoValueAtEndDate(Exception):
    """Indicates that the end of a period does not align with a value mark"""
    pass

class NotOpen(Exception):
    """Indicates the account is not open at the specified time"""
    pass
