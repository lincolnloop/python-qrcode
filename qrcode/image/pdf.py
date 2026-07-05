import os
from pathlib import Path

import qrcode.image.base


class PdfImage(qrcode.image.base.BaseImage):
    """
    PDF image builder

    Creates a QR-code image as a PDF document, without any third-party
    dependency. The PDF only contains filled rectangles, which is exactly
    what a QR library needs.
    """

    kind = "PDF"
    allowed_kinds = ("PDF",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._module_cols: dict[int, list[int]] = {}

    def new_image(self, **kwargs):
        return self

    def drawrect(self, row, col):
        self._module_cols.setdefault(row, []).append(col)

    def _rects(self):
        """
        Yield the dark modules as PDF rectangle operators, merging
        horizontal runs of modules into single rectangles.

        PDF coordinates start in the bottom-left corner with y pointing
        up, so image rows are flipped vertically.
        """
        box = self.box_size
        for row, cols in sorted(self._module_cols.items()):
            y = self.pixel_size - (row + self.border + 1) * box
            cols = sorted(cols)
            start = prev = cols[0]
            for col in [*cols[1:], None]:
                if col == prev + 1:
                    prev = col
                    continue
                x = (start + self.border) * box
                yield f"{x} {y} {(prev - start + 1) * box} {box} re f"
                start = prev = col

    def save(self, stream, kind=None):
        self.check_kind(kind=kind)
        data = self._render()
        if isinstance(stream, (str, os.PathLike)):
            Path(stream).write_bytes(data)
        else:
            stream.write(data)

    def _render(self) -> bytes:
        pagesize = self.pixel_size
        content = "0 0 0 rg\n" + "\n".join(self._rects())
        content_bytes = content.encode("ascii")

        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 "
            + f"/MediaBox [0 0 {pagesize} {pagesize}] >>".encode("ascii"),
            b"<< /Type /Page /Parent 2 0 R /Resources << >> /Contents 4 0 R >>",
            f"<< /Length {len(content_bytes)} >>\nstream\n".encode("ascii")
            + content_bytes
            + b"\nendstream",
        ]

        buf = bytearray(b"%PDF-1.1\n")
        offsets = []
        for i, obj in enumerate(objects, start=1):
            offsets.append(len(buf))
            buf += f"{i} 0 obj\n".encode("ascii") + obj + b"\nendobj\n"

        xref_offset = len(buf)
        buf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
        buf += b"0000000000 65535 f \n"
        for offset in offsets:
            buf += f"{offset:010d} 00000 n \n".encode("ascii")
        buf += (
            f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")

        return bytes(buf)
