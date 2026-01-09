import runpy
from unittest import mock


def test_main_execution():
    with mock.patch("qrcode.console_scripts.main") as mock_main:
        runpy.run_module("qrcode", run_name="__main__")
        mock_main.assert_called_once()
