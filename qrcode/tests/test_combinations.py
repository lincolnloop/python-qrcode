"""Parametrised tests for all version × error-correction combinations.

Ensures that ``QRCode.make()`` completes without errors for every valid
combination of version and EC level, and that the resulting QR code has at
least the requested version.
"""

from __future__ import annotations

import pytest

import qrcode


# Selected representative versions spanning the full range (1–40).
TEST_VERSIONS = [1, 5, 10, 20, 30, 40]

EC_LEVELS = [
    qrcode.ERROR_CORRECT_L,
    qrcode.ERROR_CORRECT_M,
    qrcode.ERROR_CORRECT_Q,
    qrcode.ERROR_CORRECT_H,
]


@pytest.mark.parametrize("version", TEST_VERSIONS)
@pytest.mark.parametrize("error_correction", EC_LEVELS)
def test_make_all_combinations(version: int, error_correction: int) -> None:
    """Verify that make() succeeds for every version × EC level combination."""
    # Use data short enough to fit in the smallest configuration (v1/L = 20 chars).
    data = "Hi"

    qr = qrcode.QRCode(version=version, error_correction=error_correction)
    qr.add_data(data)
    qr.make(fit=False)

    assert qr.version == version


@pytest.mark.parametrize("version", TEST_VERSIONS)
@pytest.mark.parametrize("error_correction", EC_LEVELS)
def test_make_image_all_combinations(version: int, error_correction: int) -> None:
    """Verify that make_image() succeeds for every combination."""
    data = "Hi"

    qr = qrcode.QRCode(version=version, error_correction=error_correction)
    qr.add_data(data)
    img = qr.make_image()

    assert img is not None


@pytest.mark.parametrize("error_correction", EC_LEVELS)
def test_auto_fit_selects_minimum_version(error_correction: int) -> None:
    """When version is auto-fitted, the result should be ≥ 1."""
    qr = qrcode.QRCode(error_correction=error_correction)
    qr.add_data("A")
    qr.make()

    assert qr.version >= 1


@pytest.mark.parametrize(
    ("version", "data"),
    [
        (1, "0" * 20),  # max numeric for v1/L
        (1, "0123456789ABCDEF"),  # alphanumeric fits in v1
        (3, "A" * 50),  # longer data needs higher version
    ],
)
def test_fit_increases_version(version: int, data: str) -> None:
    """Auto-fit should select a version that can hold the given data."""
    qr = qrcode.QRCode()
    qr.add_data(data)
    qr.make()

    assert qr.version >= version


@pytest.mark.parametrize("error_correction", EC_LEVELS)
def test_mask_pattern_all_ec(
    error_correction: int, mask_pattern: int | None = None
) -> None:
    """Each EC level works with explicit mask patterns 0–7."""
    for mp in range(8):
        qr = qrcode.QRCode(
            version=1, error_correction=error_correction, mask_pattern=mp
        )
        qr.add_data("A")
        qr.make(fit=False)
