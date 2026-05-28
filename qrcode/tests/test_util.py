import pytest

from qrcode import util


def test_check_wrong_version():
    with pytest.raises(ValueError):
        util.check_version(0)

    with pytest.raises(ValueError):
        util.check_version(41)


def test_auto_fit_with_short_data(qr_code_auto_fit, sample_data_short) -> None:
    """Auto-fit fixture selects minimal version for short data."""
    import qrcode

    qr = qr_code_auto_fit
    qr.add_data(sample_data_short)
    qr.make()
    # "Hello!" is 6 chars — should fit in version 1
    assert qr.version == 1


def test_high_ec_with_basic(qr_code_high_ec, sample_data_short) -> None:
    """High EC fixture produces valid image with short data."""
    import qrcode

    qr = qr_code_high_ec
    qr.add_data(sample_data_short)
    img = qr.make_image()
    assert img is not None


def test_basic_fixture_error_correction(qr_code_basic, sample_data_short) -> None:
    """Basic fixture uses M error correction by default."""
    import qrcode

    qr = qr_code_basic
    qr.add_data(sample_data_short)
    qr.make(fit=False)
    assert qr.error_correction == qrcode.ERROR_CORRECT_M
