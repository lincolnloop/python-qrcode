import re
import datetime
import unittest
try:
    from unittest import mock
except ImportError:
    import mock

from qrcode.release import update_manpage

OPEN = '.'.join((open.__module__, open.__name__))
DATA = 'test\n.TH "date" "version" "description"\nthis'


class UpdateManpageTests(unittest.TestCase):

    @mock.patch(OPEN, new_callable=mock.mock_open, read_data='.TH invalid')
    def test_invalid_data(self, mock_file):
        update_manpage({'name': 'qrcode', 'new_version': '1.23'})
        mock_file.assert_called()
        mock_file().write.assert_not_called()

    @mock.patch(OPEN, new_callable=mock.mock_open, read_data=DATA)
    def test_not_qrcode(self, mock_file):
        update_manpage({'name': 'not-qrcode'})
        mock_file.assert_not_called()

    @mock.patch(OPEN, new_callable=mock.mock_open, read_data=DATA)
    def test_no_change(self, mock_file):
        update_manpage({'name': 'qrcode', 'new_version': 'version'})
        mock_file.assert_called()
        mock_file().write.assert_not_called()

    @mock.patch(OPEN, new_callable=mock.mock_open, read_data=DATA)
    def test_change(self, mock_file):
        update_manpage({'name': 'qrcode', 'new_version': '3.11'})
        expected = re.split(r'([^\n]*(?:\n|$))', DATA)[1::2]
        expected[1] = expected[1].replace('version', '3.11').replace(
            'date', datetime.datetime.now().strftime('%-d %b %Y'))
        mock_file().write.has_calls([mock.call(line) for line in expected])
