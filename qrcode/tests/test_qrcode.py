import io
import unittest
from unittest import mock

import qrcode
import qrcode.util
from qrcode.exceptions import DataOverflowError
from qrcode.image.base import BaseImage
from qrcode.tests.consts import UNICODE_TEXT
from qrcode.util import MODE_8BIT_BYTE, MODE_ALPHA_NUM, MODE_NUMBER, QRData


class QRCodeTests(unittest.TestCase):
    def test_basic(self):
        qr = qrcode.QRCode(version=1)
        qr.add_data("a")
        qr.make(fit=False)

    def test_large(self):
        qr = qrcode.QRCode(version=27)
        qr.add_data("a")
        qr.make(fit=False)

    def test_invalid_version(self):
        self.assertRaises(ValueError, qrcode.QRCode, version=41)

    def test_invalid_border(self):
        self.assertRaises(ValueError, qrcode.QRCode, border=-1)

    def test_overflow(self):
        qr = qrcode.QRCode(version=1)
        qr.add_data("abcdefghijklmno")
        self.assertRaises(DataOverflowError, qr.make, fit=False)

    def test_add_qrdata(self):
        qr = qrcode.QRCode(version=1)
        data = QRData("a")
        qr.add_data(data)
        qr.make(fit=False)

    def test_fit(self):
        qr = qrcode.QRCode()
        qr.add_data("a")
        qr.make()
        self.assertEqual(qr.version, 1)
        qr.add_data("bcdefghijklmno")
        qr.make()
        self.assertEqual(qr.version, 2)

    def test_mode_number(self):
        qr = qrcode.QRCode()
        qr.add_data("1234567890123456789012345678901234", optimize=0)
        qr.make()
        self.assertEqual(qr.version, 1)
        self.assertEqual(qr.data_list[0].mode, MODE_NUMBER)

    def test_mode_alpha(self):
        qr = qrcode.QRCode()
        qr.add_data("ABCDEFGHIJ1234567890", optimize=0)
        qr.make()
        self.assertEqual(qr.version, 1)
        self.assertEqual(qr.data_list[0].mode, MODE_ALPHA_NUM)

    def test_regression_mode_comma(self):
        qr = qrcode.QRCode()
        qr.add_data(",", optimize=0)
        qr.make()
        self.assertEqual(qr.data_list[0].mode, MODE_8BIT_BYTE)

    def test_mode_8bit(self):
        qr = qrcode.QRCode()
        qr.add_data("abcABC" + UNICODE_TEXT, optimize=0)
        qr.make()
        self.assertEqual(qr.version, 1)
        self.assertEqual(qr.data_list[0].mode, MODE_8BIT_BYTE)

    def test_mode_8bit_newline(self):
        qr = qrcode.QRCode()
        qr.add_data("ABCDEFGHIJ1234567890\n", optimize=0)
        qr.make()
        self.assertEqual(qr.data_list[0].mode, MODE_8BIT_BYTE)

    def test_make_image_with_wrong_pattern(self):
        with self.assertRaises(TypeError):
            qrcode.QRCode(mask_pattern="string pattern")

        with self.assertRaises(ValueError):
            qrcode.QRCode(mask_pattern=-1)

        with self.assertRaises(ValueError):
            qrcode.QRCode(mask_pattern=42)

    def test_mask_pattern_setter(self):
        qr = qrcode.QRCode()

        with self.assertRaises(TypeError):
            qr.mask_pattern = "string pattern"

        with self.assertRaises(ValueError):
            qr.mask_pattern = -1

        with self.assertRaises(ValueError):
            qr.mask_pattern = 8

    def test_qrcode_bad_factory(self):
        with self.assertRaises(TypeError):
            qrcode.QRCode(image_factory="not_BaseImage")  # type: ignore

        with self.assertRaises(AssertionError):
            qrcode.QRCode(image_factory=dict)  # type: ignore

    def test_qrcode_factory(self):
        class MockFactory(BaseImage):
            drawrect = mock.Mock()
            new_image = mock.Mock()

        qr = qrcode.QRCode(image_factory=MockFactory)
        qr.add_data(UNICODE_TEXT)
        qr.make_image()
        self.assertTrue(MockFactory.new_image.called)
        self.assertTrue(MockFactory.drawrect.called)

    def test_optimize(self):
        qr = qrcode.QRCode()
        text = "A1abc12345def1HELLOa"
        qr.add_data(text, optimize=4)
        qr.make()
        self.assertEqual(
            [d.mode for d in qr.data_list],
            [
                MODE_8BIT_BYTE,
                MODE_NUMBER,
                MODE_8BIT_BYTE,
                MODE_ALPHA_NUM,
                MODE_8BIT_BYTE,
            ],
        )
        self.assertEqual(qr.version, 2)

    def test_optimize_short(self):
        qr = qrcode.QRCode()
        text = "A1abc1234567def1HELLOa"
        qr.add_data(text, optimize=7)
        qr.make()
        self.assertEqual(len(qr.data_list), 3)
        self.assertEqual(
            [d.mode for d in qr.data_list],
            [MODE_8BIT_BYTE, MODE_NUMBER, MODE_8BIT_BYTE],
        )
        self.assertEqual(qr.version, 2)

    def test_optimize_longer_than_data(self):
        qr = qrcode.QRCode()
        text = "ABCDEFGHIJK"
        qr.add_data(text, optimize=12)
        self.assertEqual(len(qr.data_list), 1)
        self.assertEqual(qr.data_list[0].mode, MODE_ALPHA_NUM)

    def test_optimize_size(self):
        text = "A1abc12345123451234512345def1HELLOHELLOHELLOHELLOa" * 5

        qr = qrcode.QRCode()
        qr.add_data(text)
        qr.make()
        self.assertEqual(qr.version, 10)

        qr = qrcode.QRCode()
        qr.add_data(text, optimize=0)
        qr.make()
        self.assertEqual(qr.version, 11)

    def test_qrdata_repr(self):
        data = b"hello"
        data_obj = qrcode.util.QRData(data)
        self.assertEqual(repr(data_obj), repr(data))

    def test_print_ascii_stdout(self):
        qr = qrcode.QRCode()
        with mock.patch("sys.stdout") as fake_stdout:
            fake_stdout.isatty.return_value = None
            self.assertRaises(OSError, qr.print_ascii, tty=True)
            self.assertTrue(fake_stdout.isatty.called)

    def test_print_ascii(self):
        qr = qrcode.QRCode(border=0)
        f = io.StringIO()
        qr.print_ascii(out=f)
        printed = f.getvalue()
        f.close()
        expected = "\u2588\u2580\u2580\u2580\u2580\u2580\u2588"
        self.assertEqual(printed[: len(expected)], expected)

        f = io.StringIO()
        f.isatty = lambda: True
        qr.print_ascii(out=f, tty=True)
        printed = f.getvalue()
        f.close()
        expected = (
            "\x1b[48;5;232m\x1b[38;5;255m" + "\xa0\u2584\u2584\u2584\u2584\u2584\xa0"
        )
        self.assertEqual(printed[: len(expected)], expected)

    def test_print_tty_stdout(self):
        qr = qrcode.QRCode()
        with mock.patch("sys.stdout") as fake_stdout:
            fake_stdout.isatty.return_value = None
            self.assertRaises(OSError, qr.print_tty)
            self.assertTrue(fake_stdout.isatty.called)

    def test_print_tty(self):
        qr = qrcode.QRCode()
        f = io.StringIO()
        f.isatty = lambda: True
        qr.print_tty(out=f)
        printed = f.getvalue()
        f.close()
        BOLD_WHITE_BG = "\x1b[1;47m"
        BLACK_BG = "\x1b[40m"
        WHITE_BLOCK = BOLD_WHITE_BG + "  " + BLACK_BG
        EOL = "\x1b[0m\n"
        expected = (
            BOLD_WHITE_BG + "  " * 23 + EOL + WHITE_BLOCK + "  " * 7 + WHITE_BLOCK
        )
        self.assertEqual(printed[: len(expected)], expected)

    def test_get_matrix(self):
        qr = qrcode.QRCode(border=0)
        qr.add_data("1")
        self.assertEqual(qr.get_matrix(), qr.modules)

    def test_get_matrix_border(self):
        qr = qrcode.QRCode(border=1)
        qr.add_data("1")
        matrix = [row[1:-1] for row in qr.get_matrix()[1:-1]]
        self.assertEqual(matrix, qr.modules)

    def test_negative_size_at_construction(self):
        self.assertRaises(ValueError, qrcode.QRCode, box_size=-1)

    def test_negative_size_at_usage(self):
        qr = qrcode.QRCode()
        qr.box_size = -1
        self.assertRaises(ValueError, qr.make_image)
