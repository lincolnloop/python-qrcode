"""Regression tests for QR code visual output determinism.

These tests verify that the same input always produces identical output,
regardless of environment or timing. They cover PNG (PIL), PNG (pypng), and SVG
formats.
"""

from __future__ import annotations

import hashlib
import io

import pytest

import qrcode


def _png_hash(img_bytes: bytes) -> str:
    """Return a short SHA-256 hex digest of image bytes."""
    return hashlib.sha256(img_bytes).hexdigest()[:16]


class TestPngDeterminism:
    """Verify that PNG QR output is deterministic for the same input."""

    def test_pil_deterministic(self) -> None:
        """Same data + config → identical PIL PNG bytes on repeated calls."""
        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_M)
        qr.add_data("Hello, world!")
        qr.make()

        buf_a = io.BytesIO()
        img_a = qr.make_image()
        img_a.save(buf_a)

        buf_b = io.BytesIO()
        img_b = qr.make_image()
        img_b.save(buf_b)

        assert _png_hash(buf_a.getvalue()) == _png_hash(buf_b.getvalue())

    def test_pil_dimensions(self) -> None:
        """PIL PNG pixel size matches expected (width + 2*border) * box_size."""
        border = 4
        box_size = 10
        version = 1  # 21×21 modules
        qr = qrcode.QRCode(
            version=version,
            error_correction=qrcode.ERROR_CORRECT_M,
            border=border,
            box_size=box_size,
        )
        qr.add_data("test")
        img = qr.make_image()

        expected = (21 + 2 * border) * box_size  # 290
        assert img.pixel_size == expected

    def test_pil_different_versions_produce_different_output(self) -> None:
        """Different QR versions must produce visually distinct images."""
        data = "A" * 10  # fits easily in v2 and v3

        qr1 = qrcode.QRCode(version=2, error_correction=qrcode.ERROR_CORRECT_M)
        qr1.add_data(data)
        img1 = qr1.make_image()
        buf1 = io.BytesIO()
        img1.save(buf1)

        qr2 = qrcode.QRCode(version=3, error_correction=qrcode.ERROR_CORRECT_M)
        qr2.add_data(data)
        img2 = qr2.make_image()
        buf2 = io.BytesIO()
        img2.save(buf2)

        assert _png_hash(buf1.getvalue()) != _png_hash(buf2.getvalue())


class TestPypngDeterminism:
    """Verify that pypng QR output is deterministic."""

    def test_pure_deterministic(self) -> None:
        """Same data + config → identical pypng bytes on repeated calls."""
        from qrcode.image.pure import PyPNGImage

        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_M)
        qr.add_data("Hello, world!")
        qr.make()

        buf_a = io.BytesIO()
        img_a = qr.make_image(image_factory=PyPNGImage)
        img_a.save(buf_a)

        buf_b = io.BytesIO()
        img_b = qr.make_image(image_factory=PyPNGImage)
        img_b.save(buf_b)

        assert _png_hash(buf_a.getvalue()) == _png_hash(buf_b.getvalue())


class TestSvgDeterminism:
    """Verify that SVG QR output is deterministic and well-formed."""

    def test_svg_deterministic(self) -> None:
        """Same data + config → identical SVG bytes on repeated calls."""
        from qrcode.image.svg import SvgImage

        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_M)
        qr.add_data("Hello, world!")
        qr.make()

        buf_a = io.BytesIO()
        img_a = qr.make_image(image_factory=SvgImage)
        img_a.save(buf_a)

        buf_b = io.BytesIO()
        img_b = qr.make_image(image_factory=SvgImage)
        img_b.save(buf_b)

        assert _png_hash(buf_a.getvalue()) == _png_hash(buf_b.getvalue())

    def test_svg_basic_xml_structure(self) -> None:
        """SVG output contains expected XML elements."""
        from qrcode.image.svg import SvgImage

        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_M)
        qr.add_data("test")
        img = qr.make_image(image_factory=SvgImage)
        buf = io.BytesIO()
        img.save(buf)

        svg_str = buf.getvalue().decode("utf-8")
        assert "<?xml" in svg_str
        assert "<svg" in svg_str
        assert "</svg>" in svg_str
        assert "xmlns=" in svg_str

    def test_svg_fragment_no_xml_decl(self) -> None:
        """SvgFragmentImage produces no XML declaration."""
        from qrcode.image.svg import SvgFragmentImage

        qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_M)
        qr.add_data("test")
        img = qr.make_image(image_factory=SvgFragmentImage)
        buf = io.BytesIO()
        img.save(buf)

        svg_str = buf.getvalue().decode("utf-8")
        assert "<?xml" not in svg_str
        assert "<svg" in svg_str or "xmlns" in svg_str


class TestEcdeterminism:
    """Verify that different error correction levels produce distinct output."""

    def test_ec_levels_produce_different_images(self) -> None:
        """Different EC levels → visually different QR codes."""
        data = "Hello!"
        hashes = []

        for ec in (
            qrcode.ERROR_CORRECT_L,
            qrcode.ERROR_CORRECT_M,
            qrcode.ERROR_CORRECT_Q,
            qrcode.ERROR_CORRECT_H,
        ):
            qr = qrcode.QRCode(version=1, error_correction=ec)
            qr.add_data(data)
            img = qr.make_image()
            buf = io.BytesIO()
            img.save(buf)
            hashes.append(_png_hash(buf.getvalue()))

        # All four should be distinct
        assert len(set(hashes)) == 4, (
            f"Not all EC levels produced unique images: {hashes}"
        )
