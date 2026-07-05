import io
import re

import pytest

import qrcode
from qrcode.image import pdf
from qrcode.tests.consts import UNICODE_TEXT


def make_pdf_image(**kwargs):
    qr = qrcode.QRCode(**kwargs)
    qr.add_data(UNICODE_TEXT)
    return qr.make_image(image_factory=pdf.PdfImage)


def render_bytes(img):
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue()


def test_render_pdf():
    data = render_bytes(make_pdf_image())
    assert data.startswith(b"%PDF-")
    assert data.rstrip().endswith(b"%%EOF")


def test_render_pdf_wrong_kind():
    img = make_pdf_image()
    with pytest.raises(ValueError):
        img.save(io.BytesIO(), kind="PNG")


def test_render_pdf_to_path(tmp_path):
    img = make_pdf_image()
    target = tmp_path / "qr.pdf"
    img.save(str(target))
    assert target.read_bytes().startswith(b"%PDF-")
    target2 = tmp_path / "qr2.pdf"
    img.save(target2)
    assert target2.read_bytes() == target.read_bytes()


def test_pdf_structure():
    """The stream length and the xref offsets must match the actual layout."""
    data = render_bytes(make_pdf_image())

    match = re.search(rb"<< /Length (\d+) >>\nstream\n", data)
    assert match
    stream_end = match.end() + int(match.group(1))
    assert data[stream_end:].startswith(b"\nendstream")

    match = re.search(rb"startxref\n(\d+)\n%%EOF", data)
    assert match
    assert data[int(match.group(1)) :].startswith(b"xref")

    offsets = re.findall(rb"(\d{10}) 00000 n ", data)
    for num, offset in enumerate(offsets, start=1):
        assert data[int(offset) :].startswith(b"%d 0 obj" % num)


def test_pdf_geometry_matches_qr_matrix():
    """Rectangles in the PDF must reproduce the QR matrix, in PDF's
    bottom-up coordinate system."""
    box_size = 10
    qr = qrcode.QRCode(box_size=box_size, border=4)
    qr.add_data(UNICODE_TEXT)
    data = render_bytes(qr.make_image(image_factory=pdf.PdfImage))

    matrix = qr.get_matrix()  # includes the border
    size = len(matrix)
    pagesize = size * box_size

    content = re.search(rb"stream\n(.*?)\nendstream", data, re.S).group(1).decode()
    seen = [[False] * size for _ in range(size)]
    for x, y, w, h in re.findall(r"(\d+) (\d+) (\d+) (\d+) re", content):
        x, y, w, h = int(x), int(y), int(w), int(h)
        assert h == box_size
        assert w % box_size == 0
        row = (pagesize - y - box_size) // box_size
        for col in range(x // box_size, (x + w) // box_size):
            seen[row][col] = True

    assert seen == [[bool(module) for module in row] for row in matrix]
