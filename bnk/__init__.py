"""bnk - simple financial analysis with incomplete information."""

import logging
import logging.config

# This needs to live here, before bnk imports
logging.config.fileConfig('logging.conf')

from bnk import parse
from bnk.parse import read_bnk_data
from bnk.views import AsciiView, NativeView
