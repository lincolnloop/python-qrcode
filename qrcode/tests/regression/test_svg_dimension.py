from __future__ import annotations

import io
import re
from typing import TYPE_CHECKING

import pytest

import qrcode
from qrcode.image import svg
from qrcode.tests.consts import UNICODE_TEXT

if TYPE_CHECKING:
    from qrcode.image.base import BaseImageWithDrawer


@pytest.mark.parametrize(
    "image_factory",
    [
        svg.SvgFragmentImage,
        svg.SvgImage,
        svg.SvgFillImage,
        svg.SvgPathImage,
        svg.SvgPathFillImage,
    ],
)
def test_svg_no_width_height(image_factory: BaseImageWithDrawer) -> None:
    """Test that SVG output doesn't have width and height attributes."""
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)

    # Create a svg with the specified factory and (optional) module drawer
    img = qr.make_image(image_factory=image_factory)
    svg_str = img.to_string().decode("utf-8")

    # Check that width and height attributes are not present in the SVG tag
    svg_tag_match = re.search(r"<svg[^>]*>", svg_str)
    assert svg_tag_match, "SVG tag not found"

    svg_tag = svg_tag_match.group(0)
    assert "width=" not in svg_tag, "width attribute should not be present"
    assert "height=" not in svg_tag, "height attribute should not be present"

    # Check that viewBox is present and uses pixels (no mm suffix)
    viewbox_match = re.search(r'viewBox="([^"]*)"', svg_tag)
    assert viewbox_match, "viewBox attribute not found"
    viewbox = viewbox_match.group(1)
    assert "mm" not in viewbox, "viewBox should use pixels, not mm"

    # Check that inner elements use pixels (no mm suffix)
    assert "mm" not in svg_str, "SVG elements should use pixels, not mm"
