import io

import qrcode
from qrcode.image import svg
from qrcode.image.styles.moduledrawers.svg import SvgRoundedModuleDrawer
from decimal import Decimal
from qrcode.tests.consts import UNICODE_TEXT


class SvgImageWhite(svg.SvgImage):
    background = "white"


def test_render_svg():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=svg.SvgImage)
    img.save(io.BytesIO())


def test_render_svg_path():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=svg.SvgPathImage)
    img.save(io.BytesIO())


def test_render_svg_fragment():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=svg.SvgFragmentImage)
    img.save(io.BytesIO())


def test_svg_string():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=svg.SvgFragmentImage)
    file_like = io.BytesIO()
    img.save(file_like)
    file_like.seek(0)
    assert file_like.read() in img.to_string()


def test_render_svg_with_background():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=SvgImageWhite)
    img.save(io.BytesIO())


def test_svg_circle_drawer():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=svg.SvgPathImage, module_drawer="circle")
    img.save(io.BytesIO())


def test_svg_rounded_module_drawer():
    """Test that the SvgRoundedModuleDrawer works correctly."""
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)

    # Test with default parameters
    module_drawer = SvgRoundedModuleDrawer()
    img = qr.make_image(image_factory=svg.SvgPathImage, module_drawer=module_drawer)
    img.save(io.BytesIO())

    # Test with custom radius_ratio
    module_drawer = SvgRoundedModuleDrawer(radius_ratio=Decimal("0.5"))
    img = qr.make_image(image_factory=svg.SvgPathImage, module_drawer=module_drawer)
    img.save(io.BytesIO())

    # Test with custom size_ratio
    module_drawer = SvgRoundedModuleDrawer(size_ratio=Decimal("0.8"))
    img = qr.make_image(image_factory=svg.SvgPathImage, module_drawer=module_drawer)
    img.save(io.BytesIO())

    # Test with both custom parameters
    module_drawer = SvgRoundedModuleDrawer(
        radius_ratio=Decimal("0.3"), size_ratio=Decimal("0.9")
    )
    img = qr.make_image(image_factory=svg.SvgPathImage, module_drawer=module_drawer)
    img.save(io.BytesIO())
