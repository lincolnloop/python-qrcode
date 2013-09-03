from pymaging import Image
from pymaging.colors import RGB
from pymaging.formats import registry
from pymaging.shapes import Line
from pymaging.webcolors import Black, White
from pymaging_png.png import PNG

import qrcode.image.base


class PymagingImage(qrcode.image.base.BaseImage):
    """
    pymaging image builder, default format is PNG.
    """
    kind = "PNG"

    def __init__(self, *args, **kwargs):
        """
        Register PNG with pymaging.
        """
        registry.formats = []
        registry.names = {}
        registry._populate()
        registry.register(PNG)

        super(PymagingImage, self).__init__(*args, **kwargs)

    def new_image(self, **kwargs):
        return Image.new(RGB, self.pixel_size, self.pixel_size, White)

    def drawrect(self, row, col):
        (x, y), (x2, y2) = self.pixel_box(row, col)
        for r in range(self.box_size):
            line_y = y + r
            line = Line(x, line_y, x2, line_y)
            self._img.draw(line, Black)

    def save(self, stream, kind=None):
        self._img.save(stream, self.checked_kind(kind))

    def checked_kind(self, kind=None):
        kind = super(PymagingImage, self).checked_kind(kind)
        # pymaging (pymaging_png at least) uses lower case for the type.
        kind = kind.lower()
        if kind != 'png':
            raise ValueError(
                "Only currently supporting PNG generation for pymaging")
        return kind
