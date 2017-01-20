"""Account groups and groupings"""

from bnk import account
import datetime as dt
import operator

class Group(object):
    """A group of related accounts, e.g., 'liquid' accounts or
    'retirement' accounts.  Membership to one group does not perclude
    membership to another."""

    def __init__(self, name, iterable):
        self._members = tuple(iterable)
        self._name = name


class MetaAccount(account.Account):
    """A single account that captures all the transactions/valuations of
    a set of other accounts.  This is useful to get the performance of
    an entire portolio"""

    def __init__(self, name, contributors):
        openings = [(act._topen, act) for act in contributors]
        openings.sort(key=operator.itemgetter(0))
        account.Account.__init__(self, name, openings[0][0])

        contributors = [a[1] for a in openings]  # contribtors sorted by start date
        all_value_marks = set([v.t for v in contributors[0]._values])

        for act in contributors:
            before_opening = {d for d in all_value_marks if d <= act._topen}
            after_opening = all_value_marks - before_opening
            after_opening.intersection_update({v.t for v in act._values})
            all_value_marks = before_opening.union(after_opening)

        # opening date will get a value from the account.Account.__init__, discard it here
        all_value_marks.discard(self._topen)
        value_marks_list = list(all_value_marks)
        value_marks_list.sort()

        for act in contributors:
            for t in act._transactions:
                t.add_to_account(self)

        for date in value_marks_list:
            v = 0.0
            for act in contributors:
                if date > act._topen:
                    actv, msg = act.get_value(date)
                    v += actv
                # otherwise, add 0...
            #print("Marking",date, v)
            self.mark_value(account.Value(date, v))

        self._group = Group(contributors, name)
        
        #print("Meta Account:", self._values)
        #print("Meta Account:", self._transactions)
