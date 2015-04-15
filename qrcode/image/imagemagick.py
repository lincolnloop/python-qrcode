# Needed on case-insensitive filesystems
from __future__ import absolute_import

from wand.image import Image
from wand.drawing import Drawing
from wand.color import Color

import qrcode.image.base


class WandImage(qrcode.image.base.BaseImage):
    
    kind = "png"

    def new_image(self, **kwargs):
        img = Image(width=self.pixel_size, height=self.pixel_size, background=Color('white'), format=self.kind)
        return img

    def drawrect(self, row, col):
        (x1, y1), (x2, y2) = self.pixel_box(row, col)
        with Drawing() as draw:
            draw.rectangle(x1, y1, x2, y2)
            draw(self._img)

    def save(self, stream, kind=None):
        self._img.save(stream)

    def __getattr__(self, name):
        return getattr(self._img, name)



__author__ = 'waen'
