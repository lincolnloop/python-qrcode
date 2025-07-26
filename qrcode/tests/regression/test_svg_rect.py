import io

import pytest

import qrcode
from qrcode.image import svg
from qrcode.tests.consts import UNICODE_TEXT


@pytest.mark.parametrize(
    "image_factory",
    [
        svg.SvgFillImage,
        svg.SvgFragmentImage,
        svg.SvgImage,
        svg.SvgPathFillImage,
        # svg.SvgPathImage,  # Result does not contain <rect elements
    ],
)
def test_svg_no_namespace_prefix(image_factory: svg.SvgFragmentImage):
    """
    Test that SVG output doesn't contain <svg:rect> elements.

    This regression test ensures that rect elements in SVG output are rendered as
    <rect> without the svg: namespace prefix, which can cause rendering issues in
    browsers, when loaded in HTML.

    https://github.com/lincolnloop/python-qrcode/issues/353
    https://github.com/lincolnloop/python-qrcode/issues/317
    """
    # Create a QR code
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)

    img = qr.make_image(image_factory=image_factory)
    f = io.BytesIO()
    img.save(f)
    svg_content = f.getvalue().decode("utf-8")

    # Check that there are no <svg:rect> elements in the output
    assert "<svg:rect" not in svg_content

    # Check that there are <rect> elements in the output
    assert "<rect" in svg_content
