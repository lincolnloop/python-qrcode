import xml.etree.ElementTree as ET
import qrcode.image.base


class SvgFragmentImage(qrcode.image.base.BaseImage):
    """SVG image builder

    Creates a QR-code image as a SVG document fragment.
    Ignores the {box_size} parameter, making the QR-code boxes
    1mm square."""

    _SVG_namespace = "http://www.w3.org/2000/svg"

    def __init__(self, border, width, box_size):
        super(SvgFragmentImage, self).__init__(border, width, box_size)
        self.kind = "SVG"
        ET.register_namespace("svg", self._SVG_namespace)
        self._img = self._svg()

    def drawrect(self, row, col):
        self._img.append(self._rect(row, col))

    def save(self, stream, kind=None):
        if kind is not None and kind != self.kind:
            raise ValueError("Cannot set SVG image type to " + kind)
        self._write(stream)

    def _svg(self, tag = ET.QName(_SVG_namespace, "svg")):
        dimension = "%dmm" % (2 * self.border + self.width)
        return ET.Element(tag, version="1.1",
                          width=dimension, height=dimension)

    def _rect(self, row, col, tag=ET.QName(_SVG_namespace, "rect")):
        return ET.Element(tag,
                          x="%dmm" % (self.border + col),
                          y="%dmm" % (self.border + row),
                          width="1mm", height="1mm")

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, xml_declaration=False)


class SvgImage(SvgFragmentImage):
    """Standalone SVG image builder

    Creates a QR-code image as a standalone SVG document."""

    def __init__(self, border, width, box_size):
        super(SvgImage, self).__init__(border, width, box_size)

    def _svg(self):
        svg = super(SvgImage, self)._svg(tag="svg")
        svg.set("xmlns", self._SVG_namespace)
        return svg

    def _rect(self, row, col):
        return super(SvgImage, self)._rect(row, col, tag="rect")

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, encoding="UTF-8",
                                        xml_declaration=True)
