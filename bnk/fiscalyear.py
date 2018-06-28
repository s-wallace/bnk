"""Functions for dealing with periods in the fiscal year.

name_of_ returns a string representation of period, etc
end_of_  returns the date of the end of the period
start_of_ returns the date of the start of the period
"""
import datetime as dt
from bnk.account import Period


def name_of_quarter(date):
    """Return the name of the quarter containing the specified date."""
    return "Q{0}-{1}".format(1 + (date.month - 1) // 3, date.year)


def end_of_quarter(date):
    """Return the end date of the quarter containing the specified date."""
    month = (1 + (date.month - 1) // 3) * 3
    if month == 3 or month == 12:
        day = 31
    else:
        day = 30
    return dt.date(date.year, month, day)


def end_of_completed_quarter(date):
    """Return the quarter end date that is on or before the specified date."""
    qse = [(3, 31), (6, 30), (9, 30), (12, 31)]

    # is it the given day?
    d_md = (date.month, date.day)

    if d_md in qse:
        return date

    zquarter = ((date.month - 1) // 3)  # zero based quarter
    prevzq = (zquarter - 1) % 4     # previous zero-based quarter

    year = date.year
    if prevzq == 3:    # Q4
        year -= 1

    return dt.date(year, *qse[prevzq])


def period_of_preceeding_quarter(date):
    """Return the Period of the most recently completed quarter.

    Arguments:
       date - (datetime.date) the most recently completed quarter
           is the last quarter that ends on or before this day.
    """
    lcq = end_of_completed_quarter(date)
    q_before = end_of_completed_quarter(lcq - dt.timedelta(1))

    name = "Q{0:d}-{1:d}".format((lcq.month // 3), date.year)
    return Period(q_before, lcq, name)


def quarters(fromdate, todate):
    """Generate periods (quarters) whose enddates occur in the given time span.

    Arguments:
      fromdate - (datetime.date) a date within the first quarter produced
        by this iterator.
      todate - (dateime.date) a date on or after the end of the last quarter
        produced by this iterator.
    """
    def pqy(qend_i):
        """Return -1 if the quarter end date is 3,31, else return 0."""
        if qend_i == 0:
            return -1
        return 0

    qends = [(3, 31), (6, 30), (9, 30), (12, 31)]
    year = fromdate.year
    qend_index = (fromdate.month - 1) // 3

    yield Period(dt.date(year + pqy(qend_index), *qends[qend_index - 1]),
                 dt.date(year, *qends[qend_index]),
                 "Q{0:d}-{1:d}".format(qend_index + 1, year))

    while True:
        qend_index += 1
        if qend_index == 4:
            year += 1
            qend_index = 0
        nextqstart = dt.date(year + pqy(qend_index), *qends[qend_index - 1])
        nextqend = dt.date(year, *qends[qend_index])
        if nextqstart < todate:
            yield Period(nextqstart, nextqend,
                         "Q{0:d}-{1:d}".format(qend_index + 1, year))
        else:
            break


def standard_periods(date):
    """Create a list of standard periods for the specified 'end' date.

    Standard periods include:
     - preceeding quarter
     - ytd (unless preceeding quarter is 4)
     - one year
     - three year
     - five year
     - ten year (if preceeding quarter is 4)
     - lifetime

    Arguments:
      date - (datetime.date) the endpoint anchor for the periods, this
             must be an quarter end (3/31, 6/30, 9/30 or 12/31).
    """
    periods = []
    d_md = (date.month, date.day)
    qse = [(3, 31), (6, 30), (9, 30), (12, 31)]

    try:
        qindex = qse.index(d_md)
    except ValueError:
        raise ValueError("Reports should have and end of quarter date")

    periods.append(period_of_preceeding_quarter(date))
    if qindex != 3:  # Q1-3
        periods.append(Period(dt.date(date.year - 1, 12, 31),
                              date, "Year to Date"))
    periods.append(Period(dt.date(date.year - 1, date.month, date.day),
                          date, "One Year"))
    periods.append(Period(dt.date(date.year - 3, date.month, date.day),
                          date, "Three Year"))
    periods.append(Period(dt.date(date.year - 5, date.month, date.day),
                          date, "Five Year"))
    if qindex == 3:  # Q4
        periods.append(Period(dt.date(date.year - 10, date.month, date.day),
                              date, "Ten Year"))

    periods.append(Period(None, date, "Lifetime"))

    return periods
