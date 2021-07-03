# Needed on case-insensitive filesystems
from __future__ import absolute_import

from numpy import ones, uint8

import qrcode.image.base


class NpImage(qrcode.image.base.BaseImage):

    """NumPy image for QR code."""

    def __init__(self, *args, **kwargs):
        super(NpImage, self).__init__(*args, **kwargs)

    def new_image(self, **kwargs):
        """Build the image class."""
        return ones((self.pixel_size, self.pixel_size, 3), dtype=uint8) * 255

    def drawrect(self, row, col):
        """Draw a single rectangle of the QR code."""
        (x, y), (x2, _) = self.pixel_box(row, col)
        for r in range(self.box_size):
            self._img[y + r, x:x2 + 1, :] = 0

    def save(self, stream, kind=None):
        raise NotImplementedError

    def __getattr__(self, name):
        return getattr(self._img, name)

    def __getitem__(self, ind):
        return self._img[ind]
