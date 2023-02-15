import pytest
import unittest

from qrcode import util


class UtilTests(unittest.TestCase):
    def test_check_wrong_version(self):
        with pytest.raises(ValueError):
            util.check_version(0)

        with pytest.raises(ValueError):
            util.check_version(41)
