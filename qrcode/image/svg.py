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
