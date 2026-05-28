"""Shared pytest fixtures for the qrcode test suite."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import qrcode


@pytest.fixture
def dummy_image() -> tempfile.NamedTemporaryFile:
    """Create a 1×1 red pixel PNG in a temporary file.

    Returns:
        A :class:`tempfile.NamedTemporaryFile` containing the image data.
    """
    # Must import here as PIL might be not installed
    from PIL import Image

    # A 1x1 Red Pixel
    dummy_image = Image.new("RGBA", (1, 1), (255, 0, 0, 255))

    # Save the image to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as temp_file:
        dummy_image.save(temp_file.name)
        yield temp_file


# ---------------------------------------------------------------------------
# QRCode fixtures — different configurations for reuse across test files
# ---------------------------------------------------------------------------


@pytest.fixture
def qr_code_basic() -> qrcode.QRCode:
    """QRCode instance with version 1, error correction M (default)."""
    import qrcode

    return qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_M)


@pytest.fixture
def qr_code_high_ec() -> qrcode.QRCode:
    """QRCode instance with maximum error correction level H."""
    import qrcode

    return qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_H)


@pytest.fixture
def qr_code_auto_fit() -> qrcode.QRCode:
    """QRCode instance without a fixed version (auto-fits to data)."""
    import qrcode

    return qrcode.QRCode()


# ---------------------------------------------------------------------------
# Data fixtures — sample strings for encoding tests
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_data_short() -> str:
    """Short string that fits in QR version 1."""
    return "Hello!"


@pytest.fixture
def sample_data_long() -> str:
    """Longer string requiring a higher QR version."""
    return "The quick brown fox jumps over the lazy dog. " * 5
