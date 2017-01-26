"""bnk - simple financial analysis with incomplete information"""


from bnk import parse
from bnk.parse import read_bnk_data

def read_records(record_strings):
    return parse.read_bnk_data(record_strings)['Account']
