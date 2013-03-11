from pymaging import Image
from pymaging.colors import RGBA
from pymaging.formats import registry
from pymaging.shapes import Line
from pymaging.webcolors import Black, White
from pymaging_png.png import PNG

import qrcode.image.base

class PymagingImage(qrcode.image.base.BaseImage):
    """pymaging image builder, default format is PNG."""

    def __init__(self, border, width, box_size):
        if Image is None:
            raise NotImplementedError("pymaging not available")
        super(PymagingImage, self).__init__(border, width, box_size)

        self.kind = "png"

        # Register PNG with pymaging
        registry.formats = []
        registry.names = {}
        registry._populate()
        registry.register(PNG)

        pixelsize = (self.width + self.border * 2) * self.box_size
        self._img = Image.new(pixelsize, pixelsize, White, RGBA)

    def drawrect(self, row, col):
        x = (col + self.border) * self.box_size
        y = (row + self.border) * self.box_size

        for r in range(self.box_size):
            line = Line(x, y + r, x + self.box_size - 1, y + r)
            self._img.draw(line, Black)

    def save(self, stream, kind=None):
        if kind is None:
            kind = self.kind
        self._img.save_to_path(stream, kind)
