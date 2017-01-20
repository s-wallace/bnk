"""bnk record string parser"""

import sys
import pdb
import datetime as dt
from bnk.account import Account, Value, Transaction

class NonZeroSumError(Exception):
    pass

class Record():
    """A Record read from a record string that can be added to an account"""

    def __init__(self, act, r, date, lineno=None):
        self._a = act
        self._r = r
        self._ln = lineno
        self._d = date

    def lineno(self):
        return self._ln
    def account(self):
        return self._a
    def record(self):
        return self._r
    def date(self):
        return self._d

    def __eq__(self, other):
        return (self._a == other._a and self._r == other._r)

    def __repr__(self):
        return "R: %s @line: %d"%(str(self._r), self._ln)

reserved = {
    'open' : 'OPEN',
    'close': 'CLOSE',
    'from' : 'FROM',
    'until' : 'UNTIL',
    'during' : 'DURING',
    'balances' : 'BALANCES'
}
tokens = ['SEP', 'YEAR', 'DATESPEC', 'NUMBER', 'QUARTER',
          'ID', 'RPAREN', 'LPAREN', 'TRANSFER'] + list(reserved.values())

Q = {'1': ((1, 1), (3, 31)),
     '2': ((4, 1), (6, 30)),
     '3': ((7, 1), (9, 30)),
     '4': ((10, 1), (12, 31))}

t_SEP = r'\-\-+'
t_ignore = '[\t ]+'
t_ignore_COMMENT = r'//.*'
t_RPAREN = r'\)'
t_LPAREN = r'\('
t_TRANSFER = r'->'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_DATESPEC(t):
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
    #if len(t.value) >= 1 and t.value[-1] == '.':
    #    t.value = int(t.value[:-1]+'00')
    #elif len(t.value) >= 2 and t.value[-2] == '.':
    #    t.value = int(t.value[:-2] + t.value[-1:] + '0')
    #elif len(t.value) >= 3 and t.value[-3] == '.':
    #    t.value = int(t.value[:-3] + t.value[-2:])
    #else:
    #    t.value = int(t.value + '00')
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

def t_error(t):
    print("Broken lexing! '%s'"%t.value[0])
    raise SyntaxError(t)

import ply.lex as lex
lexer = lex.lex()

def is_new_account_name(name):
    return not name in lexer.ACCOUNTS

def build_record(account, r, date, lineno):
    if not account in lexer.ACCOUNTS:
        print("WARNING!",
              "No Opening Date for account '%s' (line: %d)"%(account, lineno),
              file=sys.stderr)

        lexer.ACCOUNTS[account] = Account(account,
                                          dt.date.min + dt.timedelta(days=1))

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

    items = [build_record(act, \
                          Transaction(t[1][0], t[1][1], amt), t[1][0], lineno)
             for (act, amt, lineno) in t[3]]

    amts = sum([i.record().amount for i in items])
    if abs(amts) > 1e-10:
        raise NonZeroSumError("Transactions must sum to zero (%e) @line %d"%
                              (amts, t.lexer.lineno))
    t[0] = items

def p_statement_datespec_balances(t):
    'statement : DATESPEC BALANCES SEP balances'
    t[0] = []
    for (act, val, lineno) in t[4]:
        t[0].append(build_record(act, Value(t[1], val), t[1], lineno))

def make_account(name, opening, t):
    if not is_new_account_name(name):
        pdb.set_trace()
        raise SyntaxError("Can't open an existing account! %s line:%d"
                          (name, t.lineno(3)))

    lexer.ACCOUNTS[name] = Account(name, opening)

def p_statement_open(t):
    'statement : DATESPEC OPEN ID'
    name = t[3]
    if not is_new_account_name(name):
        # TODO, could use SyntaxError with better error handling...
        raise ValueError("Bad Account Name? %s line:%d"%(name, t.lineno(3)))


    opening = dt.date(t[1].year, t[1].month, t[1].day)
    make_account(name, opening, t)

    #t[0] = [Record(name, lexer.ACCOUNTS[name], t.lineno(5))]
    t[0] = []

def p_statement_close(t):
    'statement : DATESPEC CLOSE ID'
    name = t[3]
    if is_new_account_name(name):
        raise SyntaxError("Bad Account Name? %s line:%d"%(name, t.lineno(3)))
    closing = dt.date(t[1].year, t[1].month, t[1].day)
    lexer.ACCOUNTS[name].set_closing(closing)
    t[0] = []

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
    'transaction : ID TRANSFER ID NUMBER'
    t[0] = [(t[1], -t[4], t.lineno(2)),
            (t[3], t[4], t.lineno(2))]

def p_daterange_ds_ds(t):
    'daterange : FROM DATESPEC UNTIL DATESPEC'
    t[0] = (dt.date(t[2].year, t[2].month, t[2].day),
            dt.date(t[4].year, t[4].month, t[4].day))

def p_daterange_quarter(t):
    'daterange : DURING QUARTER'
    t[0] = t[2]

def p_daterange_year(t):
    'daterange : DURING YEAR'
    t[0] = t[2]

def p_error(t):
    # get the line of data:
    line = lexer.lexdata.splitlines()[t.lexer.lineno]

    s = SyntaxError("Unexpected token: '%s' on line %d '%s'"%(t.value,
                                                              t.lexer.lineno,
                                                              line))
    s.lineno = t.lexer.lineno
    raise s

import ply.yacc as yacc
parser = yacc.yacc()


def parse(string):
    lexer.lineno = 0
    lexer.ACCOUNTS = {}
    result = parser.parse(string)
    return result
