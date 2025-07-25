from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import qrcode

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("back_color", ["TransParent", "red", (255, 195, 235)])
def test_qrcode_clear_resets_size(tmp_path: Path):
    """
    Test that QRCode.clear() properly resets the QRCode object.

    Regression test for:

        QRCode class not resizing down between runs
        https://github.com/lincolnloop/python-qrcode/issues/392
    """
    test1_path = tmp_path / "test1.png"
    test2_path = tmp_path / "test2.png"
    test3_path = tmp_path / "test3.png"

    # Create a QR code instance
    qr = qrcode.QRCode(version=None)

    # Generate first QR code
    qr.add_data("https://example.com/")
    qr.make(fit=True)
    img1 = qr.make_image()
    img1.save(test1_path)

    # Clear and generate second QR code with different data
    qr.clear()
    qr.add_data("https://example.net/some/other/path")
    qr.make(fit=True)
    img2 = qr.make_image()
    img2.save(test2_path)

    # Clear and generate third QR code with same data as first
    qr.clear()
    qr.add_data("https://example.com/")
    qr.make(fit=True)
    img3 = qr.make_image()
    img3.save(test3_path)

    # Check that the first and third QR codes are identical.
    with test1_path.open("rb") as file1, test3_path.open("rb") as file3:
        assert file1.read() == file3.read(), (
            "First and third QR codes should be identical after clearing"
        )
