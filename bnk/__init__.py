"""bnk - simple financial analysis with incomplete information."""

import logging
import logging.config

# This needs to live here, before bnk imports
logging.config.fileConfig('logging.conf')

# these imports must occur after logging is configured, but
# violate PEP8...
from bnk import parse                          # noqa: E402
from bnk.parse import read_bnk_data            # noqa: E402
from bnk.views import AsciiView, NativeView    # noqa: E402

__all__ = [parse, read_bnk_data, AsciiView, NativeView]

_bnklog = logging.getLogger('bnk')
