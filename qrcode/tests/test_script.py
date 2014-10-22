try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from unittest import mock
except ImportError:
    import mock

from qrcode.console_scripts import main


class ScriptTest(unittest.TestCase):

    @mock.patch('os.isatty', lambda *args: True)
    @mock.patch('qrcode.main.QRCode.print_ascii')
    def test_isatty(self, mock_print_ascii):
        main(['testtext'])
        mock_print_ascii.assert_called_with(tty=True)

    @mock.patch('os.isatty', lambda *args: False)
    @mock.patch('sys.stdout')
    def test_piped(self, mock_stdout):
        main(['testtext'])

    @mock.patch('os.isatty', lambda *args: True)
    @mock.patch('qrcode.main.QRCode.print_ascii')
    def test_stdin(self, mock_print_ascii):
        mock_stdin = mock.Mock()
        mock_stdin.configure_mock(**{'read.return_value': 'testtext'})
        with mock.patch('sys.stdin', mock_stdin) as stdin:
            main([])
            self.assertTrue(stdin.read.called)
        mock_print_ascii.assert_called_with(tty=True)

    @mock.patch('os.isatty', lambda *args: True)
    @mock.patch('qrcode.main.QRCode.print_ascii')
    def test_optimize(self, mock_print_ascii):
        main('testtext --optimize 0'.split())

    @mock.patch('sys.stdout')
    def test_factory(self, mock_stdout):
        main('testtext --factory svg'.split())

    @mock.patch('sys.stderr')
    def test_bad_factory(self, mock_stderr):
        self.assertRaises(SystemExit, main, 'testtext --factory fish'.split())
