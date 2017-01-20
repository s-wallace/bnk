"""bnk - simple financial analysis with incomplete information"""

import sys
from bnk import parse

def read_records(record_strings):
    """Read records

    Arguments:
      a record_string to read

    Returns:
     dictionary mapping account names -> account isntances
    """

    if not isinstance(record_strings, str): return None

    result = parse.parse(record_strings)
    for rec in result:
        try:
            account = parse.lexer.ACCOUNTS[rec.account()]
            rec.record().add_to_account(account)

        except ValueError as e:
            print("** Failed to update account with parsed data **",
                  file=sys.stderr)
            print("  Record: %s"%rec, file=sys.stderr)
            print("  Reason: %s"%e, file=sys.stderr)
            raise e

    return dict(parse.lexer.ACCOUNTS)
