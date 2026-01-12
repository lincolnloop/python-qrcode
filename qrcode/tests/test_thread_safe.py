from unittest import mock
import qrcode
from qrcode import util


def test_best_fit_passes_copy_to_bisect():
    """
    Verify that best_fit passes a copy of BIT_LIMIT_TABLE to bisect_left
    to ensure thread safety in Python 3.13+.
    """
    qr = qrcode.QRCode()
    qr.add_data("test data")

    # Identify the global table being used
    original_table = util.BIT_LIMIT_TABLE[qr.error_correction]

    with mock.patch("qrcode.main.bisect_left") as mock_bisect:
        # Mock return value to be a valid version number to avoid side effects
        mock_bisect.return_value = 1

        qr.best_fit()

        assert mock_bisect.called

        # Check arguments: bisect_left(a, x, lo=0, hi=len(a), *, key=None)
        # We are interested in 'a' (the list)
        args, _ = mock_bisect.call_args
        passed_table = args[0]

        # Verify content matches
        assert passed_table == original_table

        # Verify it is a NEW object (copy), not the original global list
        # This confirms the thread-safety fix
        assert passed_table is not original_table
