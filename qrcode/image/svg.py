from decimal import Decimal
# On Python 2.6 must install lxml since the older xml.etree.ElementTree
# version can not be used to create SVG images.
try:
    import lxml.etree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import qrcode.image.base


class SvgFragmentImage(qrcode.image.base.BaseImage):
    """
    SVG image builder

    Creates a QR-code image as a SVG document fragment.
    A box_size of 10 (default) equals 1mm.
    """

    _SVG_namespace = "http://www.w3.org/2000/svg"
    kind = "SVG"

    def __init__(self, *args, **kwargs):
        ET.register_namespace("svg", self._SVG_namespace)
        super(SvgFragmentImage, self).__init__(*args, **kwargs)
        # Save the mm size, for example the default boxsize of 10 is '1mm'.
        self.mm_size = self.mm(self.box_size)

    def drawrect(self, row, col):
        self._img.append(self._rect(row, col))

    def mm(self, pixels, text=True):
        mm = Decimal(pixels) / 10
        if not text:
            return mm
        return '%smm' % mm

    def save(self, stream, kind=None):
        if kind is not None and kind != self.kind:
            raise ValueError("Cannot set SVG image type to " + kind)
        self._write(stream)

    def new_image(self, **kwargs):
        return self._svg()

    def _svg(self, tag=ET.QName(_SVG_namespace, "svg")):
        dimension = self.mm(self.pixel_size)
        return ET.Element(
            tag, version="1.1", width=dimension, height=dimension)

    def _rect(self, row, col, tag=ET.QName(_SVG_namespace, "rect")):
        x, y = self.pixel_box(row, col)[0]
        return ET.Element(
            tag, x=self.mm(x), y=self.mm(y),
            width=self.mm_size, height=self.mm_size)

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, xml_declaration=False)


class SvgImage(SvgFragmentImage):
    """
    Standalone SVG image builder

    Creates a QR-code image as a standalone SVG document.
    """

    def _svg(self):
        svg = super(SvgImage, self)._svg(tag="svg")
        svg.set("xmlns", self._SVG_namespace)
        return svg

    def _rect(self, row, col):
        return super(SvgImage, self)._rect(row, col, tag="rect")

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, encoding="UTF-8",
                                        xml_declaration=True)


class SvgPathImage(SvgFragmentImage):
    """
    SVG image builder with one single <path> element (removes white spaces
    between individual QR points)"""

    SCALE = 1
    UNITS = 'mm'
    QR_PATH_STYLE = 'fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:none'

    def __init__(self, border, width, box_size):
        self._points = set()
        super(SvgPathImage, self).__init__(border, width, box_size)

    def _svg(self, tag=ET.QName("svg")):
        dimension = self.width * self.SCALE + (2 * self.border * self.SCALE)

        svg = ET.Element(
            tag,
            version="1.1",
            width="{0}{units}".format(dimension, units=self.UNITS),
            height="{0}{units}".format(dimension, units=self.UNITS),
            viewBox="0 0 {s} {s}".format(s=dimension)
        )
        svg.set("xmlns", self._SVG_namespace)
        return svg

    def drawrect(self, row, col):
        # (x, y)
        self._points.add((col, row))

    def _generate_subpaths(self):
        """Generates individual QR points as subpaths"""

        scale = self.SCALE

        for point in self._points:
            x_base = point[0] * scale + self.border * scale
            y_base = point[1] * scale + self.border * scale

            yield 'M {x0} {y0} L {x0} {y1} L {x1} {y1} L {x1} {y0} z'.format(
                x0=x_base,
                y0=y_base,
                x1=x_base + scale,
                y1=y_base + scale
            )

    def make_path(self):
        subpaths = self._generate_subpaths()

        return ET.Element(
            ET.QName("path"),
            style=self.QR_PATH_STYLE,
            d=' '.join(subpaths),
            id="qr-path"
        )

    def _write(self, stream):
        self._img.append(self.make_path())
        ET.ElementTree(self._img).write(stream,
                                        encoding="UTF-8", xml_declaration=True)
