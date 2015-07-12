# Needed on case-insensitive filesystems
from __future__ import absolute_import

# Try to import PIL in either of the two ways it can be installed.
try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    import Image
    import ImageDraw

import qrcode.image.base


class PilImage(qrcode.image.base.BaseImage):
    """
    PIL image builder, default format is PNG.
    """
    kind = "PNG"

    def new_image(self, **kwargs):
        img = Image.new("RGBA", (self.pixel_size, self.pixel_size),
            self.back_color)
        self._idr = ImageDraw.Draw(img)
        return img

    def drawrect(self, row, col, fill_color):
        box = self.pixel_box(row, col)
        self._idr.rectangle(box, fill=fill_color)

    def save(self, stream, kind=None):
        if kind is None:
            kind = self.kind
        self._img.save(stream, kind)

    def __getattr__(self, name):
        return getattr(self._img, name)
