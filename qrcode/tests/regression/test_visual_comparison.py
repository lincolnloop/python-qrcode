from __future__ import annotations

import io
import re
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

import qrcode
from qrcode.compat.etree import ET
from qrcode.image import pure, svg

if TYPE_CHECKING:
    from collections.abc import Sequence


DATA = "HELLO WORLD"
VERSION = 1
BOX_SIZE = 10
BORDER = 4
WIDTH = 21  # (4 * VERSION + 17) modules for a version 1 code

# Reference module matrices generated with Nayuki's QR Code generator, an
# independent implementation of the QR Code spec:
#
# https://github.com/nayuki/QR-Code-generator/blob/9a217d443937f60cc56c1458c39a211d7f2d3af5/python/qrcodegen.py
#
# QrCode.encode_segments(QrSegment.make_segments("HELLO WORLD"),
#                        QrCode.Ecc.LOW, 1, 1, <mask>, False)
REFERENCE_MODULES = {
    0: (
        "111111100010101111111",
        "100000100000101000001",
        "101110101010001011101",
        "101110100000101011101",
        "101110100101101011101",
        "100000100111001000001",
        "111111101010101111111",
        "000000001010000000000",
        "111011111010111000100",
        "111011001011000010001",
        "111010110111001011000",
        "100110010101110101110",
        "000111110111001110101",
        "000000001010001000101",
        "111111101000100101100",
        "100000101010001101000",
        "101110101100101111111",
        "101110100011010100010",
        "101110101011011101001",
        "100000101001110001011",
        "111111101011011100001",
    ),
    7: (
        "111111100010101111111",
        "100000101010101000001",
        "101110101011001011101",
        "101110100000101011101",
        "101110101111101011101",
        "100000101110001000001",
        "111111101010101111111",
        "000000001000000000000",
        "110100110011101110110",
        "111011001011000010001",
        "101000100101011001010",
        "101111011100111100111",
        "000111110111001110101",
        "000000001000011010111",
        "111111101001101100101",
        "100000100010001101000",
        "101110100110111101101",
        "101110101010011101011",
        "101110100011011101001",
        "100000101011100011001",
        "111111101010010101000",
    ),
}


def make_qr(mask_pattern: int) -> qrcode.QRCode:
    qr = qrcode.QRCode(
        version=VERSION,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=BOX_SIZE,
        border=BORDER,
        mask_pattern=mask_pattern,
    )
    qr.add_data(DATA)
    qr.make(fit=False)
    return qr


def assert_matrix(actual: Sequence[Sequence[bool]], mask_pattern: int) -> None:
    expected = [
        [cell == "1" for cell in row] for row in REFERENCE_MODULES[mask_pattern]
    ]
    assert actual == expected


@pytest.mark.parametrize("mask_pattern", [0, 7])
def test_pil_render_matches_reference(mask_pattern: int):
    """
    Every dark module of the PIL-rendered image must land exactly on the
    independently generated reference matrix.

    https://github.com/lincolnloop/python-qrcode/issues/410
    """
    pytest.importorskip("PIL.Image", reason="PIL is not installed")

    img = make_qr(mask_pattern).make_image().get_image().convert("RGB")

    offset = BORDER * BOX_SIZE
    actual = [
        [
            img.getpixel(
                (
                    offset + col * BOX_SIZE + BOX_SIZE // 2,
                    offset + row * BOX_SIZE + BOX_SIZE // 2,
                )
            )
            == (0, 0, 0)
            for col in range(WIDTH)
        ]
        for row in range(WIDTH)
    ]
    assert_matrix(actual, mask_pattern)

    # The quiet zone stays light: sample the first pixel of each corner.
    last = (WIDTH + 2 * BORDER) * BOX_SIZE - 1
    for corner in [(0, 0), (last, 0), (0, last), (last, last)]:
        assert img.getpixel(corner) == (255, 255, 255)


def test_pil_render_custom_colors():
    """
    fill_color/back_color map to the dark/light modules of the reference
    matrix, not merely to any non-white pixels.

    https://github.com/lincolnloop/python-qrcode/issues/410
    """
    pytest.importorskip("PIL.Image", reason="PIL is not installed")
    fill, back = (55, 95, 35), (255, 195, 235)

    img = (
        make_qr(0)
        .make_image(fill_color=fill, back_color=back)
        .get_image()
        .convert("RGB")
    )

    offset = BORDER * BOX_SIZE
    for row in range(WIDTH):
        for col in range(WIDTH):
            px = img.getpixel(
                (
                    offset + col * BOX_SIZE + BOX_SIZE // 2,
                    offset + row * BOX_SIZE + BOX_SIZE // 2,
                )
            )
            if REFERENCE_MODULES[0][row][col] == "1":
                assert px == fill, f"module ({row}, {col})"
            else:
                assert px == back, f"module ({row}, {col})"


@pytest.mark.parametrize("mask_pattern", [0, 7])
def test_pypng_render_matches_reference(mask_pattern: int):
    """
    The pure-Python PNG backend must encode the same modules as the
    reference matrix; the saved PNG is decoded back and sampled at the
    center of every module.

    https://github.com/lincolnloop/python-qrcode/issues/410
    """
    png = pytest.importorskip("png", reason="PyPNG is not installed")

    img = make_qr(mask_pattern).make_image(image_factory=pure.PyPNGImage)
    stream = io.BytesIO()
    img.save(stream)

    width_px, height_px, rows, _info = png.Reader(bytes=stream.getvalue()).read()
    assert width_px == height_px == (WIDTH + 2 * BORDER) * BOX_SIZE
    pixels = list(rows)

    offset = BORDER * BOX_SIZE
    actual = [
        [
            pixels[offset + row * BOX_SIZE + BOX_SIZE // 2][
                offset + col * BOX_SIZE + BOX_SIZE // 2
            ]
            == 0
            for col in range(WIDTH)
        ]
        for row in range(WIDTH)
    ]
    assert_matrix(actual, mask_pattern)


def svg_module_positions(svg_bytes: bytes) -> set[tuple[int, int]]:
    """
    Return the (row, col) grid positions of every dark module encoded in an
    SVG document, whether modules were emitted as <rect> elements or merged
    into a single <path>.
    """
    root = ET.fromstring(svg_bytes)
    positions = set()
    for element in root.iter():
        tag = element.tag.rpartition("}")[2]
        if tag == "rect" and element.get("x", "").endswith("mm"):
            # x/y are in mm at 0.1 pixel each (box_size 10 -> 1mm).
            positions.add(
                (
                    int(Decimal(element.get("y")[:-2])) - BORDER,
                    int(Decimal(element.get("x")[:-2])) - BORDER,
                )
            )
        elif tag == "path" and element.get("d"):
            for x, y in re.findall(r"M([\d.]+),([\d.]+)H", element.get("d")):
                positions.add((int(Decimal(y)) - BORDER, int(Decimal(x)) - BORDER))
    return positions


@pytest.mark.parametrize(
    "image_factory",
    [
        svg.SvgImage,
        svg.SvgFragmentImage,
        svg.SvgFillImage,
        svg.SvgPathImage,
        svg.SvgPathFillImage,
    ],
)
@pytest.mark.parametrize("mask_pattern", [0, 7])
def test_svg_render_matches_reference(image_factory, mask_pattern: int):
    """
    Both SVG module shapes (per-module <rect> elements and the single
    <path> variants) must encode the reference matrix exactly.

    https://github.com/lincolnloop/python-qrcode/issues/410
    """
    img = make_qr(mask_pattern).make_image(image_factory=image_factory)
    stream = io.BytesIO()
    img.save(stream)

    positions = svg_module_positions(stream.getvalue())
    expected = {
        (row, col)
        for row, line in enumerate(REFERENCE_MODULES[mask_pattern])
        for col, cell in enumerate(line)
        if cell == "1"
    }
    assert positions == expected
