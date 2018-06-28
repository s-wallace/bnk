"""bnk record-string parser."""

import logging
from collections import OrderedDict
import datetime as dt
import ply.lex as lex
import ply.yacc as yacc
from bnk.account import Account, Value, Transaction
from bnk.groups import Group, MetaAccount

_log = logging.getLogger(__name__)


_ErrorToken = None


def last_error_token():
    """Return the token that led to the most recent error."""
    return _ErrorToken


class NonZeroSumError(Exception):
    """Exception thrown if transcactons don't sum to zero."""

    pass


class Record():
    """A Record read from a record string that can be added to an account."""

    def __init__(self, act, r, date, lineno=None):
        """Initialize a Record

        Arguments:
          act    -- account associated with the record
          r      -- the record instance itself (transaction, value, etc)
          date   -- the date assocaited with the record
          lineno -- the line number on which the record originated (if known)
        """
        self._a = act
        self._r = r
        self._ln = lineno
        self._d = date

    def lineno(self):
        """Return the linenumber of the record."""
        return self._ln

    def account(self):
        """Return the account associated with the record."""
        return self._a

    def record(self):
        """Return the record itself (transaction, value, etc)."""
        return self._r

    def date(self):
        """Return the date assocaited with the record."""
        return self._d

    def __eq__(self, other):
        return (self._a == other._a and self._r == other._r)

    def __repr__(self):
        return "R: %s @line: %d" % (str(self._r), self._ln)


reserved = {
    'open': 'OPEN',
    'group': 'GROUP',
    'meta': 'META',
    'close': 'CLOSE',
    'from': 'FROM',
    'until': 'UNTIL',
    'during': 'DURING',
    'balances': 'BALANCES'
}
tokens = ['SEP', 'YEAR', 'DATEMDY', 'NUMBER', 'QUARTER',
          'ID', 'RPAREN', 'LPAREN', 'R_ARROW'] + list(reserved.values())

Q = {'1': ((1, 1), (3, 31)),
     '2': ((4, 1), (6, 30)),
     '3': ((7, 1), (9, 30)),
     '4': ((10, 1), (12, 31))}

t_SEP = r'\-\-+'
t_ignore = '[\t ]+'
t_ignore_COMMENT = r'//.*'
t_RPAREN = r'\)'
t_LPAREN = r'\('
t_R_ARROW = r'->'


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_DATEMDY(t):
    r'\d\d-\d\d-\d\d\d\d'
    t.value = dt.date(int(t.value[6:10]),
                      int(t.value[0:2]), int(t.value[3:5]))
    return t


def t_QUARTER(t):
    r'Q[1234]-\d\d\d\d'
    year = int(t.value[3:7])
    q_se = Q[t.value[1]]
    t.value = (dt.date(year, q_se[0][0], q_se[0][1]),
               dt.date(year, q_se[1][0], q_se[1][1]))
    return t


def t_NUMBER(t):
    r'-{0,1}\d+\.{0,1}\d{0,2}'
    t.value = float(t.value)
    return t


def t_YEAR(t):
    r'\d\d\d\d'
    year = int(t.value)
    t.value = (dt.date(year, 1, 1),
               dt.date(year, 12, 31))


def t_ID(t):
    r'[\w:]+'
    t.type = reserved.get(t.value, 'ID')    # Check for reserved words
    return t


def t_error(t):     # No doc string for this t_ function  noqa: D103
    global _ErrorToken
    _log.critical("Broken lexing! '%s'", str(t.value[0]))
    _ErrorToken = t
    raise SyntaxError(t)


def is_new_name(name):
    """Determine if an (account/group) name is already known."""
    if name in _lexer.ACCOUNTS or name in _lexer.GROUPS or name in _lexer.META:
        return False
    return True


def build_record(account, r, date, lineno, t):
    """Build a record for a specific account.

    Args:
      account - the account to receive the record
      r       - the record (e.g., transaction/value) itself
      date    - the date associated with the record
      lineno  - the linenumber where the record was found
    """
    global _ErrorToken
    if account not in _lexer.ACCOUNTS:
        if _lexer.strict:
            _log.critical("No Opening Date for account '%s' (line: %d)",
                          account, lineno)
            _ErrorToken = t
            raise LookupError(t)

        else:

            _log.warning("No Opening Date for account '%s' (line: %d)",
                         account, lineno)

            _lexer.ACCOUNTS[account] = Account(account, dt.date.min +
                                               dt.timedelta(days=1))

    return Record(account, r, date, lineno)


# list of statements
def p_statements_state_statements(t):
    'statements : statement statements'
    t[0] = t[1] + t[2]


def p_statements_null(t):
    'statements :'
    t[0] = []


# individual statements
def p_statement_transactions(t):
    'statement : daterange SEP transactions'
    items = [build_record(act,
                          Transaction(t[1][0], t[1][1], amt),
                          t[1][0], lineno, t)
             for (act, amt, lineno) in t[3]]

    amts = sum([i.record().amount for i in items])
    if abs(amts) > 1e-10:
        raise NonZeroSumError("Transactions must sum to zero (%e) @line %d" %
                              (amts, t.lexer.lineno))
    t[0] = items


def p_statement_datespec_balances(t):
    'statement : DATEMDY BALANCES SEP balances'
    t[0] = []
    for (act, val, lineno) in t[4]:
        t[0].append(build_record(act, Value(t[1], val), t[1], lineno, t))


def p_statement_oneline_balance(t):
    'statement : DATEMDY ID NUMBER'
    t[0] = [build_record(t[2],
                         Value(t[1], t[3]), t[1], t.lineno(3), t)]


def p_statement_oneline_transaction(t):
    'statement : daterange ID R_ARROW ID NUMBER'
    t[0] = []
    t[0].append(build_record(t[2], Transaction(t[1][0], t[1][1], -t[5]),
                             t[1][0], t.lineno(5), t))
    t[0].append(build_record(t[4], Transaction(t[1][0], t[1][1], t[5]),
                             t[1][0], t.lineno(5), t))


def p_statement_oneline_transaction_single_date(t):
    'statement : DATEMDY ID R_ARROW ID NUMBER'
    t[0] = []
    t[0].append(build_record(t[2], Transaction(t[1], t[1], -t[5]),
                             t[1], t.lineno(5), t))
    t[0].append(build_record(t[4], Transaction(t[1], t[1], t[5]),
                             t[1], t.lineno(5), t))


def make_account(name, opening, lineno):
    """Create a new account with the specified name and opening date"""
    if not is_new_name(name):
        raise SyntaxError("Can't open an existing account! %s line:%d"
                          (name, lineno))

    _lexer.ACCOUNTS[name] = Account(name, opening)


def make_group(name, members, lineno):
    """Create a new group with the specified name and members"""
    if not is_new_name(name):
        raise SyntaxError("?")
    _lexer.GROUPS[name] = Group(name, [resolve_name(n) for n in members])


def resolve_name(n):
    """Get the account/group/meta-account with the specified name."""
    if n in _lexer.ACCOUNTS:
        return _lexer.ACCOUNTS[n]
    if n in _lexer.META:
        return _lexer.META[n]  # at this point, this is actually a group...
    if n in _lexer.GROUPS:
        return _lexer.GROUPS[n]
    raise ValueError("Unknown name! %s" % n)


def make_meta(name, members, lineno):
    """Create a new meta placeholder with the specified name and members"""
    if not is_new_name(name):
        raise SyntaxError("?")
    # initially, this needs to be created as a group
    # until records are all processed
    _lexer.META[name] = Group(name, [_lexer.ACCOUNTS[n] for n in members])


def p_statement_open(t):
    'statement : DATEMDY OPEN ID'
    name = t[3]
    if not is_new_name(name):
        # TODO, could use SyntaxError with better error handling...
        raise ValueError("Bad Account Name? %s line:%d" % (name, t.lineno(3)))

    opening = dt.date(t[1].year, t[1].month, t[1].day)
    make_account(name, opening, t.lineno(3))

    t[0] = []


def p_statement_close(t):
    'statement : DATEMDY CLOSE ID'
    name = t[3]
    if is_new_name(name):
        raise SyntaxError("Bad Account Name? %s line:%d" % (name, t.lineno(3)))
    closing = dt.date(t[1].year, t[1].month, t[1].day)
    _lexer.ACCOUNTS[name].set_closing(closing)
    t[0] = []


def p_statement_group(t):
    'statement : GROUP ID R_ARROW LPAREN groupmembers RPAREN'
    if not is_new_name(t[2]):
        raise ValueError("Bad Group Name? %s line:%d" % (t[2], t.lineno(2)))
    make_group(t[2], t[5], t.lineno(2))
    t[0] = []


def p_statement_meta(t):
    'statement : META ID R_ARROW LPAREN groupmembers RPAREN'
    if not is_new_name(t[2]):
        raise ValueError("Bad Group Name? %s line:%d" % (t[2], t.lineno(2)))
    make_meta(t[2], t[5], t.lineno(2))
    t[0] = []


def p_groupmembers_recursive(t):
    'groupmembers : ID groupmembers'
    t[0] = [t[1]] + t[2]


def p_groupmembers_basecase(t):
    'groupmembers : ID'
    t[0] = [t[1]]


def p_balances_bal_bals(t):
    'balances : balance balances'
    t[0] = [t[1]] + t[2]


def p_balances_bal(t):
    'balances : balance'
    t[0] = [t[1]]


def p_balance(t):
    'balance : ID NUMBER'
    t[0] = (t[1], t[2], t.lineno(2))


def p_balance_rng(t):
    'balance : ID LPAREN NUMBER NUMBER NUMBER RPAREN'
    t[0] = (t[1], (t[3], t[4], t[5]), t.lineno(1))


def p_transactions_basecase(t):
    'transactions : transaction'
    t[0] = t[1]


def p_transactions_recursive(t):
    'transactions : transaction transactions'
    t[0] = t[1] + t[2]


def p_transaction(t):
    'transaction : ID NUMBER'
    t[0] = [(t[1], t[2], t.lineno(2))]


def p_transfer(t):
    'transaction : ID R_ARROW ID NUMBER'
    t[0] = [(t[1], -t[4], t.lineno(2)),
            (t[3], t[4], t.lineno(2))]


def p_daterange_ds_ds(t):
    'daterange : FROM DATEMDY UNTIL DATEMDY'
    t[0] = (dt.date(t[2].year, t[2].month, t[2].day),
            dt.date(t[4].year, t[4].month, t[4].day))


def p_daterange_quarter(t):
    'daterange : DURING QUARTER'
    t[0] = t[2]


def p_daterange_year(t):
    'daterange : DURING YEAR'
    t[0] = t[2]


def p_error(t):  # No doc string for this p_ function  noqa: D103
    global _ErrorToken
    # get the line of data:
    line = _lexer.lexdata.splitlines()[t.lexer.lineno]

    _log.critical("In p_error!")
    s = SyntaxError("Unexpected token: '%s' on line %d '%s'" % (t.value,
                                                                t.lexer.lineno,
                                                                line))
    s.lineno = t.lexer.lineno
    _ErrorToken = t
    raise s


_parser = yacc.yacc()
_lexer = lex.lex()


def read_bnk_data(record_string, carry_last=False, to_date=None, strict=False,
                  debug=0):
    """Read records.

    Arguments:
      record_string - a record_string to read
      strict - warnings trigger exceptions (default)

    Returns:
     dictionary mapping account names -> account isntances

    """
    if not isinstance(record_string, str):
        return None

    _lexer.strict = strict
    _lexer.lineno = 0
    _lexer.ACCOUNTS = {}
    _lexer.GROUPS = {}
    _lexer.META = {}
    result = _parser.parse(record_string, debug=debug)
    for rec in result:
        try:
            account = _lexer.ACCOUNTS[rec.account()]
            rec.record().add_to_account(account)

        except ValueError as e:
            _log.critical("** Failed to update account ** [%s] %s",
                          str(rec), str(e))

            raise e

    if carry_last:
        assert isinstance(to_date, dt.date)
        for a in _lexer.ACCOUNTS:
            try:
                _lexer.ACCOUNTS[a].carrylast(to_date)
            except ValueError:
                pass

    # note we need to actually create the meta accounts
    # what's in _lexer.META at this point is a Group, not a MetaAccount
    # we don't
    meta = OrderedDict([(name, MetaAccount(name, _lexer.META[name]))
                        for name in sorted(_lexer.META)])

    if carry_last:
        # change the name of meta accounts to update their
        # 'carrylast status', note that we don't actually call
        # carrylast on the metaaccount, since value is
        # propigated automagically via the childen
        for m in meta:
            cl = 0
            for account in meta[m]._group:
                if account._cl:
                    cl = max(cl, account._cl)
            if cl > 0:
                meta[m].name = meta[m].name + " [cl%d]" % cl

    return {'Account': OrderedDict([(name, _lexer.ACCOUNTS[name])
                                   for name in sorted(_lexer.ACCOUNTS)]),
            'Group': OrderedDict([(name, _lexer.GROUPS[name])
                                 for name in sorted(_lexer.GROUPS)]),
            'Meta': meta}
