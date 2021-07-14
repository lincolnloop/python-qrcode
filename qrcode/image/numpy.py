# Needed on case-insensitive filesystems
from __future__ import absolute_import

from numpy import ones, uint8
import qrcode.image.base


class NpImage(qrcode.image.base.BaseImage):

    """NumPy image for QR code."""

    kind = "PNG"
    allowed_kinds = ("PNG",)

    def new_image(self, **kwargs):
        """Build the image class."""
        return ones((self.pixel_size, self.pixel_size, 3), dtype=uint8) * 255

    def drawrect(self, row, col):
        """Draw a single rectangle of the QR code."""
        (x, y), (x2, y2) = self.pixel_box(row, col)
        self._img[y:y2 + 1, x:x2 + 1, :] = 0

    def save(self, stream, kind=None):
        """Save to PNG."""
        from zlib import crc32, compress
        from struct import pack

        self.check_kind(kind)
        h, w, _ = self._img.shape
        img = ones((h, w, 4), dtype=uint8) * 255
        img[::-1, :, :-1] = self._img
        buf = img.tobytes()
        w_byte = w * 4
        raw_data = b''.join(b'\x00' + buf[span:span + w_byte]
                            for span in range((h - 1) * w_byte, -1, -w_byte))

        def png_pk(png_tag, data):
            chunk_head = png_tag + data
            return (pack("!I", len(data))
                    + chunk_head
                    + pack("!I", 0xFFFFFFFF & crc32(chunk_head)))

        b = b''.join([
            b'\x89PNG\r\n\x1a\n',
            png_pk(b'IHDR', pack("!2I5B", w, h, 8, 6, 0, 0, 0)),
            png_pk(b'IDAT', compress(raw_data, 9)),
            png_pk(b'IEND', b'')])
        with open(stream, 'wb') as f:
            f.write(b)

    def __getattr__(self, name):
        return getattr(self._img, name)

    def __getitem__(self, ind):
        return self._img[ind]
