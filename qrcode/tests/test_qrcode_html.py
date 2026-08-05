import io
import re
from html.parser import HTMLParser

import pytest

import qrcode
from qrcode.image.html import HtmlImage
from qrcode.tests.consts import UNICODE_TEXT


class TableParser(HTMLParser):
    """
    Rebuild the QR code matrix from the generated markup.
    """

    def __init__(self, box_size, fill_color="#000000"):
        super().__init__()
        self.box_size = box_size
        self.fill_color = fill_color
        self.matrix = []
        self.tables = 0
        self.row = None
        self.row_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.tables += 1
        elif tag == "tr":
            self.row = []
            self.row_count = self.px(attrs["style"], "height") // self.box_size
        elif tag == "td":
            colspan = int(attrs.get("colspan", 1))
            assert self.px(attrs["style"], "width") == colspan * self.box_size
            dark = f"background-color:{self.fill_color}" in attrs["style"]
            self.row.extend([dark] * colspan)

    def handle_endtag(self, tag):
        if tag == "tr":
            self.matrix.extend([self.row] * self.row_count)
            self.row = None

    @staticmethod
    def px(style, prop):
        return int(re.search(rf"(?:^|;){prop}:(\d+)px", style).group(1))


def parse(html, box_size=10, fill_color="#000000"):
    parser = TableParser(box_size, fill_color)
    parser.feed(html)
    return parser


def make_html(**kwargs):
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    return qr.make_image(image_factory=HtmlImage, **kwargs).to_string()


def test_render_html():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=HtmlImage)
    img.save(io.BytesIO())


def test_html_string():
    qr = qrcode.QRCode()
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=HtmlImage)
    html = img.to_string()
    assert html.startswith("<table")
    assert html.endswith("</table>")
    assert img.get_image() == html


def test_save_binary_stream():
    img = qrcode.make(UNICODE_TEXT, image_factory=HtmlImage)
    stream = io.BytesIO()
    img.save(stream)
    assert stream.getvalue().decode() == img.to_string()


def test_save_text_stream():
    img = qrcode.make(UNICODE_TEXT, image_factory=HtmlImage)
    stream = io.StringIO()
    img.save(stream)
    assert stream.getvalue() == img.to_string()


def test_save_path(tmp_path):
    img = qrcode.make(UNICODE_TEXT, image_factory=HtmlImage)
    path = tmp_path / "test.html"
    img.save(str(path))
    assert path.read_text(encoding="utf-8") == img.to_string()


def test_wrong_kind():
    img = qrcode.make(UNICODE_TEXT, image_factory=HtmlImage)
    with pytest.raises(ValueError):
        img.save(io.BytesIO(), kind="PNG")


@pytest.mark.parametrize("border", [0, 1, 4])
@pytest.mark.parametrize("box_size", [1, 7])
def test_matches_matrix(border, box_size):
    qr = qrcode.QRCode(border=border, box_size=box_size)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=HtmlImage)
    parser = parse(img.to_string(), box_size=box_size)
    assert parser.tables == 1
    assert parser.matrix == qr.get_matrix()


def test_size():
    qr = qrcode.QRCode(border=4, box_size=5)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=HtmlImage)
    size = (qr.modules_count + 8) * 5
    assert f"width:{size}px;height:{size}px" in img.to_string()


def test_colors():
    html = make_html(fill_color="#375f23", back_color="#ffc3eb")
    assert "background-color:#ffc3eb" in html
    assert "background-color:#375f23" in html
    assert parse(html, fill_color="#375f23").matrix


def test_merged_border_rows():
    qr = qrcode.QRCode(border=4)
    qr.add_data(UNICODE_TEXT)
    img = qr.make_image(image_factory=HtmlImage)
    # The border rows above and below the code collapse into a single row each.
    assert img.to_string().count("<tr") <= qr.modules_count + 2


def test_alt_and_attrib():
    html = make_html(alt="Scan me", attrib={"class": "qr-code"})
    assert 'role="img"' in html
    assert 'aria-label="Scan me"' in html
    assert 'class="qr-code"' in html


def test_escaped_attributes():
    html = make_html(alt='"><script>')
    assert "<script>" not in html
    assert 'aria-label="&quot;&gt;&lt;script&gt;"' in html
