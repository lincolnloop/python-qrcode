# Needed on case-insensitive filesystems
from __future__ import absolute_import

from numpy import full, uint8

import qrcode.image.base


class NpImage(qrcode.image.base.BaseImage):

    """NumPy image for QR code."""

    def __init__(self, border, width, box_size, *args, **kwargs):
        super(NpImage, self).__init__(border, width, box_size, *args, **kwargs)

    def new_image(self, **kwargs):
        """Build the image class."""
        return full((self.pixel_size, self.pixel_size, 3), 255, dtype=uint8)

    def drawrect(self, row, col):
        """Draw a single rectangle of the QR code."""
        (x, y), (x2, _) = self.pixel_box(row, col)
        for r in range(self.box_size):
            self._img[y + r, x:x2 + 1] = (0, 0, 0)

    def get_qimage(self, qimage):
        """To QImage."""
        height, width, color = self._img.shape
        return qimage(
            self._img.data,
            width,
            height,
            color * height,
            qimage.Format_RGB888
        )

    def save(self, stream, kind=None):
        """Do nothing."""
        pass
