from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PIL import Image, ImageDraw

import qrcode.image.base

if TYPE_CHECKING:
    from typing import IO


__all__: list[str] = [
    "PilImage",
]


class PilImage(qrcode.image.base.BaseImage):
    """PIL/Pillow image builder for QR codes.

    Generates QR code images using the Pillow library. Supports multiple output
    formats (PNG, JPEG, BMP, etc.) via the ``format`` parameter on :meth:`save`.

    The default mode is binary (1-bit) for standard black-on-white QR codes.
    Custom colors trigger RGB mode; transparent backgrounds use RGBA.

    Args:
        border: Quiet zone width in modules (passed from :class:`~qrcode.main.QRCode`).
        width: Module grid size (passed automatically).
        box_size: Pixel size per module (passed automatically).
        fill_color: Color for dark modules. Default ``"black"``. Accepts any
            Pillow-compatible color specification (string, tuple, etc.).
        back_color: Background color. Default ``"white"``. Use
            ``"transparent"`` for an alpha channel.

    Example:
        >>> import qrcode
        >>> img = qrcode.make("data", fill_color="navy", back_color="lightyellow")
        >>> img.save("qr.png")
    """

    kind = "PNG"

    def __init__(
        self,
        border: int,
        width: int,
        box_size: int,
        *args: Any,
        fill_color: str | int = "black",
        back_color: str = "white",
        **kwargs: Any,
    ) -> None:
        """Initialize the PIL image factory.

        Args:
            border: Quiet zone width in modules.
            width: Module grid size.
            box_size: Pixel size per module.
            fill_color: Color for dark modules. Default ``"black"``.
            back_color: Background color. Default ``"white"``.
            **kwargs: Additional keyword arguments (e.g. ``qrcode_modules``).
        """
        self._fill_color_arg = fill_color
        self._back_color_arg = back_color
        kwargs["fill_color"] = fill_color
        kwargs["back_color"] = back_color
        super().__init__(border, width, box_size, *args, **kwargs)

    def new_image(self, **kwargs: Any) -> Image.Image:
        """Create a new Pillow image with the appropriate mode.

        Returns:
            A PIL :class:`PIL.Image.Image` instance (mode 1, RGB, or RGBA).
        """
        if not Image:
            raise ImportError("PIL library not found.")

        back_color = kwargs.get("back_color", "white")
        fill_color = kwargs.get("fill_color", "black")

        try:
            fill_color = fill_color.lower()
            back_color = back_color.lower()
        except AttributeError:
            pass

        # L mode (1 mode) color = (r*299 + g*587 + b*114)//1000
        if fill_color == "black" and back_color == "white":
            mode = "1"
            fill_color = 0
            if back_color == "white":
                back_color = 255
        elif back_color == "transparent":
            mode = "RGBA"
            back_color = None
        else:
            mode = "RGB"

        img = Image.new(mode, (self.pixel_size, self.pixel_size), back_color)
        self.fill_color = fill_color
        self._idr = ImageDraw.Draw(img)
        return img

    def drawrect(self, row: int, col: int) -> None:
        """Draw a dark module at grid position *(row, col)*.

        Args:
            row: Row index.
            col: Column index.
        """
        box = self.pixel_box(row, col)
        self._idr.rectangle(box, fill=self.fill_color)

    def save(
        self, stream: IO[bytes] | str, kind: str | None = None, **kwargs: Any
    ) -> None:  # type: ignore[override]
        """Save the image to a file or binary stream.

        Args:
            stream: File-like object (binary mode) or file path string.
            kind: Output format (``"PNG"``, ``"JPEG"``, etc.). Falls back to
                ``self.kind`` if not specified. Also accepted as ``format``
                for backwards compatibility.
            **kwargs: Additional keyword arguments forwarded to
                :meth:`PIL.Image.Image.save`. The ``format`` key is also
                accepted as an alias for *kind*.
        """
        fmt = kwargs.pop("format", None)
        if kind is None and fmt is not None:
            kind = fmt
        if kind is None:
            kind = self.kind
        self._img.save(stream, format=kind, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying PIL image."""
        return getattr(self._img, name)
