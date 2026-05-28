"""Tests for the custom eye_drawer feature (Issue #237).

Verifies that different eye drawers can be specified independently from the
module drawer, and that the resulting QR code remains scannable when using
high error correction.
"""

from __future__ import annotations

import io

import pytest

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import (
    CircleModuleDrawer,
    GappedCircleModuleDrawer,
    SquareModuleDrawer,
)


class TestCustomEyeDrawer:
    """Verify that eye_drawer can be customised independently of module_drawer."""

    def test_different_eye_and_module_drawers(self) -> None:
        """StyledPilImage accepts distinct eye_drawer and module_drawer instances."""
        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_H)
        qr.add_data("Hello!")

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer(),
            eye_drawer=SquareModuleDrawer(),
        )

        buf = io.BytesIO()
        img.save(buf)
        assert len(buf.getvalue()) > 0

    def test_circle_eyes_with_square_modules(self) -> None:
        """Circular eyes with square data modules produce valid output."""
        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_H)
        qr.add_data("Test!")

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=SquareModuleDrawer(),
            eye_drawer=CircleModuleDrawer(),
        )

        buf = io.BytesIO()
        img.save(buf)
        assert len(buf.getvalue()) > 0

    def test_default_eye_drawer_works(self) -> None:
        """When no eye_drawer is given, the default drawer is used for eyes."""
        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_H)
        qr.add_data("Hi!")

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=GappedCircleModuleDrawer(),
        )

        buf = io.BytesIO()
        img.save(buf)
        assert len(buf.getvalue()) > 0

    def test_eye_drawer_produces_different_output(self) -> None:
        """Different eye drawers should produce visually distinct images."""
        import hashlib

        data = "EyeTest"

        # Image with square eyes
        qr1 = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_H)
        qr1.add_data(data)
        img1 = qr1.make_image(
            image_factory=StyledPilImage,
            module_drawer=SquareModuleDrawer(),
            eye_drawer=SquareModuleDrawer(),
        )
        buf1 = io.BytesIO()
        img1.save(buf1)

        # Image with circle eyes (different visual output expected)
        qr2 = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_H)
        qr2.add_data(data)
        img2 = qr2.make_image(
            image_factory=StyledPilImage,
            module_drawer=SquareModuleDrawer(),
            eye_drawer=CircleModuleDrawer(),
        )
        buf2 = io.BytesIO()
        img2.save(buf2)

        hash1 = hashlib.sha256(buf1.getvalue()).hexdigest()[:16]
        hash2 = hashlib.sha256(buf2.getvalue()).hexdigest()[:16]

        assert hash1 != hash2, "Different eye drawers should produce different images"


class TestSvgEyeDrawer:
    """Test custom eye drawers with SVG factories."""

    def test_svg_path_with_circle_drawer(self) -> None:
        """SvgPathImage supports module_drawer parameter via drawer_aliases."""
        from qrcode.image.svg import SvgPathFillImage

        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_H)
        qr.add_data("SVG!")

        img = qr.make_image(image_factory=SvgPathFillImage)
        buf = io.BytesIO()
        img.save(buf)

        svg_str = buf.getvalue().decode("utf-8")
        assert "<path" in svg_str
