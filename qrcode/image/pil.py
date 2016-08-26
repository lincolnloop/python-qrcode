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

    def new_image(self, back_color=(255,255,255)):
        img = Image.new("RGB", (self.pixel_size, self.pixel_size), back_color)
        self._idr = ImageDraw.Draw(img)
        return img

    def drawrect(self, row, col, color=None):
        if None == color:
            color = (0,0,0)
        box = self.pixel_box(row, col)
        self._idr.rectangle(box, fill=color)

    def save(self, stream, format=None, **kwargs):
        if format is None:
            format = kwargs.get("kind", self.kind)
        if "kind" in kwargs:
            del kwargs["kind"]
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)
