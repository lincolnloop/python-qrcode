import io
from decimal import Decimal

import qrcode
from qrcode.image import svg
from qrcode.image.styles.moduledrawers.svg import SvgPathCircleDrawer
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


def test_svg_path_circle_radius_at_half_size():
    qr = qrcode.QRCode(box_size=10)
    qr.add_data("example")
    img = qr.make_image(
        image_factory=svg.SvgPathImage,
        module_drawer=SvgPathCircleDrawer(size_ratio=Decimal("0.5")),
    )
    # A half-width module has a 0.5-unit diameter in the SVG viewBox.
    assert b"A0.25,0.25 " in img.to_string()
