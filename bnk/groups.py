"""Account groups and groupings."""

import logging
from bnk import account
import operator

_log = logging.getLogger(__name__)


class Group(object):
    """A group of related accounts.

    e.g., 'liquid' accounts or 'retirement' accounts.
    Membership to one group does not perclude membership to another.
    """

    def __init__(self, name, iterable):
        """Create a group with the specified name and members."""
        self._members = tuple(iterable)
        self._name = name

    def __str__(self):
        """Generate a string representation for the Group."""
        mems = ",".join((a.name for a in self._members))
        return "Group: {0:s} [{1:s}]".format(self._name, mems)

    def __getitem__(self, n):
        """Get the n-th member of the group."""
        return self._members[n]

    def __len__(self):
        """Return the number of members in the group."""
        return len(self._members)

    def __contains__(self, k):
        """Return true iff the group contains k as a member."""
        return k in self._members

    def __iter__(self):
        """Return an iterator over the group members."""
        return iter(self._members)

    def __reversed__(self):
        """Return a reversed iterator over the group members."""
        return reversed(self._members)

    def __eq__(self, other):
        """Determine if this Group is equivilant to another."""
        try:
            if self._members != other._members:
                return False
            if self._name != other._name:
                return False
            return True
        except Exception:
            pass

        return False


class MetaAccount(account.Account):
    """A single account that captures transactions/values of multiple others.

    A MetaAccount is useful to get performance of a portion of a portfolio.
    It encapsulates all the transactions and valuations of its children
    but presents itself as a 'single' entity.
    """

    def __init__(self, name, contributors):
        """Initialize a MetaAccount with specified name and child accounts."""

        openings = [(act._topen, act) for act in contributors]
        openings.sort(key=operator.itemgetter(0))
        account.Account.__init__(self, name, openings[0][0])

        # contribtors sorted by start date
        contributors = [a[1] for a in openings]
        all_value_marks = set([v.t for v in contributors[0]._values])

        _log.debug("Winnowing values for %s (initially %d)", name,
                   len(all_value_marks))

        for act in contributors:
            while_open = {d for d in all_value_marks if act.is_open(d)}
            while_closed = all_value_marks - while_open

            while_open.intersection_update({v.t for v in act._values})
            all_value_marks = while_open.union(while_closed)
            _log.debug("  - after %s: %d", act.name, len(all_value_marks))
        # opening date will get a value from the
        # account.Account.__init__, discard it here
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

            self.mark_value(account.Value(date, v))

        self._group = Group(name, contributors)
