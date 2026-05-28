from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qrcode.compat.png import PngWriter
from qrcode.image.base import BaseImage

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import IO


__all__: list[str] = [
    "PyPNGImage",
]


class PyPNGImage(BaseImage):
    """Pure Python PNG image builder using the ``pypng`` library.

    This factory requires no external image libraries beyond ``pypng``, making it
    ideal for minimal deployments or environments where Pillow is unavailable.
    Output is always grayscale 1-bit PNG (black modules on white background).

    Args:
        border: Quiet zone width in modules.
        width: Module grid size.
        box_size: Pixel size per module.

    Example:
        >>> from qrcode.image.pure import PyPNGImage
        >>> import qrcode
        >>> img = qrcode.make("data", image_factory=PyPNGImage)
        >>> img.save("qr.png")
    """

    kind = "PNG"
    allowed_kinds = ("PNG",)
    needs_drawrect = False

    def new_image(self, **kwargs: dict[str, Any]) -> Any:
        """Create a new pypng writer instance.

        Returns:
            A :class:`png.Writer` configured for grayscale 1-bit output.
        """
        if not PngWriter:
            raise ImportError("PyPNG library not installed.")

        return PngWriter(self.pixel_size, self.pixel_size, greyscale=True, bitdepth=1)

    def drawrect(self, row: int, col: int) -> None:
        """Not used — PyPNGImage writes rows directly."""

    def save(self, stream: IO[bytes] | str, kind: str | None = None) -> None:
        """Save the QR code as a PNG file.

        Args:
            stream: File-like object (binary mode) or file path string.
            kind: Ignored; only ``"PNG"`` is supported.
        """
        if isinstance(stream, str):
            stream = Path(stream).open("wb")  # noqa: SIM115
        self._img.write(stream, self.rows_iter())

    def rows_iter(self) -> Generator[list[int], None, None]:
        """Yield pixel rows for the entire QR code image.

        Each row is a list of 0/1 values (1 = white/background, 0 = dark module).
        Rows are emitted top-to-bottom including border rows before and after
        the module grid.

        Yields:
            A list of integers representing one pixel row.
        """
        yield from self.border_rows_iter()
        border_col = [1] * (self.box_size * self.border)
        for module_row in self.modules:  # type: ignore[union-attr]
            row: list[int] = (
                border_col
                + list(
                    chain.from_iterable(
                        ([not point] * self.box_size) for point in module_row
                    )
                )
                + border_col
            )
            for _ in range(self.box_size):
                yield row
        yield from self.border_rows_iter()

    def border_rows_iter(self) -> Generator[list[int], None, None]:
        """Yield the white border rows (top and bottom).

        Yields:
            A list of all-1 integers for each border pixel row.
        """
        border_row = [1] * (self.box_size * (self.width + self.border * 2))
        for _ in range(self.border * self.box_size):
            yield border_row


# Keeping this for backwards compatibility.
PymagingImage = PyPNGImage
