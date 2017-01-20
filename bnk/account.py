"""
Financial reports with incomplete information
"""

import datetime as dt
import bisect
import logging
import collections

class Account(object):
    """An Account is a black box with transactions and point values.

    It has the following properties:
      1. It has an opening date, topen. At any point
         t <= topen, the balance is 0.
      2. It has a closing date, tclose. At any point
         t > tclose, the balance is 0.
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

    def get_value(self, t):
        """Determine the account value at time t

        Return a tuple (v,info) such that:
        v is a numeric value
        info is a informative string about the value
        """

        if t < self._topen:
            return (0.0, "Not Open")
        if self._tclose and t > self._tclose:
            return (0.0, "Closed")

        for r in self._values:
            if r.t == t:
                return (r.value, "Marked")

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

        keys['start date'] = start
        keys['end date'] = end

        starti = None
        endi = None
        for (i, val) in enumerate(self._values):
            if val.t == start:
                starti = i
            elif val.t == end:
                endi = i

        # If there is a value marked at the start and end
        # time, we also know that no transactions cross
        # those boundaries.  Thus, this check should be redundant
        for trn in self._transactions:
            if trn.tstart <= start:
                assert trn.tend <= start, "Transaction spans a value mark!"
            # strictly > here since transactions are computed before values
            if trn.tend > end:
                assert trn.tstart > end, "Transaction spans a value mark!"

        if starti is None:
            keys['error'] = NoStartDate
            return keys['error']
        if endi is None:
            keys['error'] = NoEndDate
            return keys['error']
        if start < self._topen:
            keys['error'] = NotOpen
            return keys['error']

        #perf['performance'] = self.calculate_irr(svi, evi)
        keys['start balance'] = self._values[starti].value
        keys['end balance'] = self._values[endi].value

        keys['additions'] = 0
        keys['subtractions'] = 0

        # walk the transactions:
        for t in self._transactions:
            if t.tstart > start and t.tend <= end:
                if t.amount > 0.0:
                    keys['additions'] += t.amount
                else:
                    keys['subtractions'] -= t.amount

        keys['gain'] = (self._values[endi].value -
                        self._values[starti].value -
                        keys['additions'] + keys['subtractions'])

        return True


class Value(collections.namedtuple('_V', "t value")):
    """An account valuation (at a moment in time)"""

    def replicate(self, newdate):
        return Value(newdate, self.value)

    def add_to_account(self, account):
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

class NoStartDate(Exception):
    pass

class NoEndDate(Exception):
    pass

class NotOpen(Exception):
    pass
