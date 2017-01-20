from bnk.account import Period
import datetime as dt


def quarter_name(date):
    """Returns the name of the quarter containing the specified date"""
    return "Q{0}-{1}".format(1+(date.month-1)//3, date.year)

def enddate_of_quarter_containing(date):
    """Returns the end date of the quarter containing the specified date"""

    month = (1 + (date.month-1)//3) * 3
    if month == 3 or month == 12:
        day = 31
    else: day = 30
    return dt.date(date.year, month, day)

def enddate_of_last_complete_quarter(date):
    """Returns the quarter end date that is on or before the specified date"""

    qse = [(3, 31), (6, 30), (9, 30), (12, 31)]

    # is it the given day?
    d_md = (date.month, date.day)

    if d_md in qse:
        return date

    zquarter = ((date.month-1)//3) # zero based quarter
    prevzq = (zquarter - 1) % 4 # previous zero-based quarter
    if prevzq == 3: # Q4
        year = date.year - 1
    else:
        year = date.year

    return dt.date(year, *qse[prevzq])


def quarter_preceeding(date):
    """Returns a Period representing most recent quarter to
    complete on or before the specified date
    """
    lcq = enddate_of_last_complete_quarter(date)
    q_before = enddate_of_last_complete_quarter(lcq-dt.timedelta(1))

    name = "Q"+str(lcq.month//3)
    return Period(q_before, lcq, name)

def is_quarter_end(date):
    """Returns the name of the quarter ending on the given date, or None"""

    if date.month == 12 and date.day == 31:
        return "Q4"
    if date.month == 9 and date.day == 30:
        return "Q3"
    if date.month == 6 and date.day == 30:
        return "Q2"
    if date.month == 3 and date.day == 31:
        return "Q1"
    return None



def quarter_ends(fromdate, todate):
    """Creates a list of quarter ending dates that includes the time span (fromdate, todate)
    inclusive of both end points"""

    qends = [(3, 31), (6, 30), (9, 30), (12, 31)]
    year = fromdate.year
    for i, q in enumerate(qends):
        if q[0] >= fromdate.month:
            qindex = i
            yield dt.date(year, q[0], q[1])
            break

    while True:
        qindex += 1
        if qindex == 4:
            year += 1
            qindex = 0
        nextq = dt.date(year, qends[qindex][0], qends[qindex][1])
        if nextq < todate:
            yield nextq
        else:
            yield nextq
            break

def standard_periods(date):
    """Create a list of standard periods for the specified date"""

    periods = []
    d_md = (date.month, date.day)
    qse = [(3, 31), (6, 30), (9, 30), (12, 31)]

    try:
        qindex = qse.index(d_md)
    except:
        raise ValueError("Reports should have and end of quarter date")

    periods.append(quarter_preceeding(date))
    if qindex != 3: # Q1-3
        periods.append(Period(dt.date(date.year-1, 12, 31),
                              date, "Year to Date"))
    periods.append(Period(dt.date(date.year-1, date.month, date.day),
                          date, "One Year"))
    periods.append(Period(dt.date(date.year-3, date.month, date.day),
                          date, "Three Year"))
    periods.append(Period(dt.date(date.year-5, date.month, date.day),
                          date, "Five Year"))
    if qindex == 3:  # Q4
        periods.append(Period(dt.date(date.year-10, date.month, date.day),
                              date, "Ten Year"))

    periods.append(Period(None, date, "Lifetime"))

    return periods
