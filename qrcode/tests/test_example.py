import unittest
from unittest import mock

from qrcode import run_example
from PIL import Image


class ExampleTest(unittest.TestCase):
    @unittest.skipIf(not Image, "Requires PIL")
    @mock.patch("PIL.Image.Image.show")
    def runTest(self, mock_show):
        run_example()
        mock_show.assert_called_with()
