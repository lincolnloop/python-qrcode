# Needed on case-insensitive filesystems
from __future__ import absolute_import

# Try to import PIL in either of the two ways it can be installed.
try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    import Image
    import ImageDraw

from qrcode.image.base import BaseImage


class PilImage(BaseImage):
    """
    PIL image builder, default format is PNG.
    """
    kind = "PNG"

    def __init__(self, *args, **kwargs):
        super(PilImage, self).__init__(*args, **kwargs)
        if 'shape' in kwargs:
            shape = kwargs['shape'].lower()
            if shape == 'rect':
                self.shape = self._drawrect
            elif shape == 'circle':
                self.shape = self._drawcircle
            else:
                raise Exception("Invalid draw shape %s" % shape)
        else:
            self.shape = self._drawrect

    def new_image(self, back_color=(255,255,255)):
        img = Image.new("RGB", (self.pixel_size, self.pixel_size), back_color)
        self._idr = ImageDraw.Draw(img)
        return img

    def _drawrect(self, box, color):
        self._idr.rectangle(box, fill=color)

    def _drawcircle(self, box, color):
        box = [(box[0][0] - 2, box[0][1] - 2), (box[1][0] + 2, box[1][1] + 2)]
        if (color != (255,255,255)):
            self._idr.ellipse(box, fill=color)

    def drawrect(self, row, col, color=None):
        if None == color:
            color = (0,0,0)
        box = self.pixel_box(row, col)
        self.shape(box, color)

    def save(self, stream, format=None, **kwargs):
        if format is None:
            format = kwargs.get("kind", self.kind)
        if "kind" in kwargs:
            del kwargs["kind"]
        self._img.save(stream, format=format, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)
