import qrcode
import qrcode.image.svg
from qrcode.exceptions import DataOverflowError
from qrcode.util import (
    MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE)

try:
    import unittest2 as unittest
except ImportError:
    import unittest

UNICODE_TEXT = u'\u03b1\u03b2\u03b3'


class QRCodeTests(unittest.TestCase):

    def test_basic(self):
        qr = qrcode.QRCode(version=1)
        qr.add_data('a')
        qr.make(fit=False)

    def test_overflow(self):
        qr = qrcode.QRCode(version=1)
        qr.add_data('abcdefghijklmno')
        self.assertRaises(DataOverflowError, qr.make, fit=False)

    def test_fit(self):
        qr = qrcode.QRCode()
        qr.add_data('a')
        qr.make()
        self.assertEqual(qr.version, 1)
        qr.add_data('bcdefghijklmno')
        qr.make()
        self.assertEqual(qr.version, 2)

    def test_mode_number(self):
        qr = qrcode.QRCode()
        qr.add_data('1234567890123456789012345678901234')
        qr.make()
        self.assertEqual(qr.version, 1)
        self.assertEqual(qr.data_list[0].mode, MODE_NUMBER)

    def test_mode_alpha(self):
        qr = qrcode.QRCode()
        qr.add_data('ABCDEFGHIJ1234567890')
        qr.make()
        self.assertEqual(qr.version, 1)
        self.assertEqual(qr.data_list[0].mode, MODE_ALPHA_NUM)

    def test_mode_8bit(self):
        qr = qrcode.QRCode()
        qr.add_data(u'abcABC' + UNICODE_TEXT)
        qr.make()
        self.assertEqual(qr.version, 1)
        self.assertEqual(qr.data_list[0].mode, MODE_8BIT_BYTE)

    def test_render_svg(self):
        qr = qrcode.QRCode()
        qr.add_data(UNICODE_TEXT)
        qr.make_image(image_factory=qrcode.image.svg.SvgImage)
