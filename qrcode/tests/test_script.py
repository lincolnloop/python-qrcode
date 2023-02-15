import pytest
import io
import os
import sys
import unittest
from tempfile import mkdtemp
from unittest import mock

from qrcode.compat.pil import Image
from qrcode.console_scripts import commas, main


def bad_read():
    raise UnicodeDecodeError("utf-8", b"0x80", 0, 1, "invalid start byte")


class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = mkdtemp()

    def tearDown(self):
        os.rmdir(self.tmpdir)

    @mock.patch("os.isatty", lambda *args: True)
    @mock.patch("qrcode.main.QRCode.print_ascii")
    def test_isatty(self, mock_print_ascii):
        main(["testtext"])
        mock_print_ascii.assert_called_with(tty=True)

    @mock.patch("os.isatty", lambda *args: False)
    @mock.patch("sys.stdout")
    @unittest.skipIf(not Image, "Requires PIL")
    def test_piped(self, mock_stdout):
        main(["testtext"])

    @mock.patch("os.isatty", lambda *args: True)
    @mock.patch("qrcode.main.QRCode.print_ascii")
    @mock.patch("sys.stdin")
    def test_stdin(self, mock_stdin, mock_print_ascii):
        mock_stdin.buffer.read.return_value = "testtext"
        main([])
        assert mock_stdin.buffer.read.called
        mock_print_ascii.assert_called_with(tty=True)

    @mock.patch("os.isatty", lambda *args: True)
    @mock.patch("qrcode.main.QRCode.print_ascii")
    def test_stdin_py3_unicodedecodeerror(self, mock_print_ascii):
        mock_stdin = mock.Mock(sys.stdin)
        mock_stdin.buffer.read.return_value = "testtext"
        mock_stdin.read.side_effect = bad_read
        with mock.patch("sys.stdin", mock_stdin):
            # sys.stdin.read() will raise an error...
            with pytest.raises(UnicodeDecodeError):
                sys.stdin.read()
            # ... but it won't be used now.
            main([])
        mock_print_ascii.assert_called_with(tty=True)

    @mock.patch("os.isatty", lambda *args: True)
    @mock.patch("qrcode.main.QRCode.print_ascii")
    def test_optimize(self, mock_print_ascii):
        main("testtext --optimize 0".split())

    @mock.patch("sys.stdout")
    def test_factory(self, mock_stdout):
        main("testtext --factory svg".split())

    @mock.patch("sys.stderr")
    def test_bad_factory(self, mock_stderr):
        self.assertRaises(SystemExit, main, "testtext --factory fish".split())

    @mock.patch.object(sys, "argv", "qr testtext output".split())
    @unittest.skipIf(not Image, "Requires PIL")
    def test_sys_argv(self):
        main()

    @unittest.skipIf(not Image, "Requires PIL")
    def test_output(self):
        tmpfile = os.path.join(self.tmpdir, "test.png")
        main(["testtext", "--output", tmpfile])
        os.remove(tmpfile)

    @mock.patch("sys.stderr", new_callable=io.StringIO)
    @unittest.skipIf(not Image, "Requires PIL")
    def test_factory_drawer_none(self, mock_stderr):
        with pytest.raises(SystemExit):
            main("testtext --factory pil --factory-drawer nope".split())
        assert 'The selected factory has no drawer aliases' in mock_stderr.getvalue()

    @mock.patch("sys.stderr", new_callable=io.StringIO)
    def test_factory_drawer_bad(self, mock_stderr):
        with pytest.raises(SystemExit):
            main("testtext --factory svg --factory-drawer sobad".split())
        assert 'sobad factory drawer not found' in mock_stderr.getvalue()

    @mock.patch("sys.stderr", new_callable=io.StringIO)
    def test_factory_drawer(self, mock_stderr):
        main("testtext --factory svg --factory-drawer circle".split())

    def test_commas(self):
        assert commas([]) == ''
        assert commas(['A']) == 'A'
        assert commas('AB') == 'A or B'
        assert commas('ABC') == 'A, B or C'
        assert commas('ABC', joiner='and') == 'A, B and C'
