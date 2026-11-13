import io

import pytest

import qrcode
import qrcode.util
from qrcode.image.pure import PyPNGImage
from qrcode.tests.consts import UNICODE_TEXT

png = pytest.importorskip("png", reason="png is not installed")


def test_render_pypng():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=PyPNGImage)
    assert isinstance(img.get_image(), png.Writer)

    img.save(io.BytesIO())


def test_render_pypng_to_str(tmp_path):
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=PyPNGImage)
    assert isinstance(img.get_image(), png.Writer)

    expected = io.BytesIO()
    img.save(expected)

    output = tmp_path / "test_file.png"
    img.save(str(output))

    assert output.read_bytes() == expected.getvalue()
