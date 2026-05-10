"""Tests for the experimental Micro QR encoder.

These tests round-trip the generated symbols through ``zxing-cpp``
(which supports Micro QR) to verify that what we emit is decodable
by a compliant reader. ``zxing-cpp`` is an optional test dependency;
tests are skipped if it is unavailable.
"""
from __future__ import annotations

import io

import pytest

from qrcode.micro import MicroQRCode, MICRO_ECC_L, MICRO_ECC_M

zxingcpp = pytest.importorskip("zxingcpp")
PIL_Image = pytest.importorskip("PIL.Image")


def _to_pil(matrix, scale: int = 20, border: int = 4):
    n = len(matrix)
    side = (n + 2 * border) * scale
    img = PIL_Image.new("L", (side, side), 255)
    px = img.load()
    for r in range(n):
        for c in range(n):
            if matrix[r][c]:
                for dr in range(scale):
                    for dc in range(scale):
                        px[(c + border) * scale + dc, (r + border) * scale + dr] = 0
    return img


@pytest.mark.parametrize("data,expected_version", [
    ("01234567", 2),
    ("12345", 2),
    ("0123456789", 2),
    ("012345678901234567", 3),
    ("01234567890123456789012345678901234", 4),
])
def test_numeric_round_trip(data, expected_version):
    """Generated Micro QR decodes back to the original numeric payload."""
    mqr = MicroQRCode(data, error_correction=MICRO_ECC_L)
    assert mqr.version == expected_version

    results = zxingcpp.read_barcodes(_to_pil(mqr.matrix))
    assert results, f"failed to decode M{mqr.version} numeric {data!r}"
    assert results[0].text == data
    assert "Micro QR" in str(results[0].format)


def test_explicit_version():
    """Forcing version=4 produces a 17x17 symbol regardless of payload size."""
    mqr = MicroQRCode("01234", version=4, error_correction=MICRO_ECC_L)
    assert len(mqr.matrix) == 17

    results = zxingcpp.read_barcodes(_to_pil(mqr.matrix))
    assert results
    assert results[0].text == "01234"


def test_overflow_raises():
    """Data beyond the largest Micro QR variant raises a clear error."""
    with pytest.raises(ValueError, match="capacity"):
        MicroQRCode("0" * 200, error_correction=MICRO_ECC_L)


def test_non_numeric_rejected():
    """Numeric mode rejects non-digit strings up front."""
    with pytest.raises(ValueError, match="digits"):
        MicroQRCode("abc", error_correction=MICRO_ECC_L)


def test_unsupported_version():
    """M1 is not in the experimental scope yet."""
    with pytest.raises(ValueError, match="M2-M4"):
        MicroQRCode("12", version=1, error_correction=MICRO_ECC_L)


def test_invalid_ecc():
    with pytest.raises(ValueError, match="ECC"):
        MicroQRCode("123", error_correction="X")


@pytest.mark.parametrize("ecc", [MICRO_ECC_L, MICRO_ECC_M])
def test_m4_with_each_ecc(ecc):
    """M4 supports L and M (Q has its own capacity, tested elsewhere)."""
    payload = "0" * 14 if ecc == MICRO_ECC_M else "0" * 16
    mqr = MicroQRCode(payload, version=4, error_correction=ecc)
    results = zxingcpp.read_barcodes(_to_pil(mqr.matrix))
    assert results, f"failed to decode M4-{ecc}"
    assert results[0].text == payload


def test_to_ascii_dimensions():
    mqr = MicroQRCode("01234567", error_correction=MICRO_ECC_L)
    art = mqr.to_ascii(border=2)
    lines = art.split("\n")
    assert len(lines) == 13 + 2 * 2  # 13x13 with border 2
