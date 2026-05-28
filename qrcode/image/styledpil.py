from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PIL import Image

import qrcode.image.base
from qrcode.image.styles.colormasks import QRColorMask, SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import SquareModuleDrawer

if TYPE_CHECKING:
    from typing import IO


__all__: list[str] = [
    "StyledPilImage",
]


class StyledPilImage(qrcode.image.base.BaseImageWithDrawer):
    """Styled PIL image builder with colour masks and embedded images.

    Extends :class:`BaseImageWithDrawer` to support:

    - **Colour masks** — a :class:`~qrcode.image.styles.colormasks.QRColorMask`
      subclass that calculates per-pixel foreground colours (gradients, patterns,
      image-based masks). The default is :class:`~qrcode.image.styles.colormasks.SolidFillColorMask`.

    - **Module drawers** — pluggable drawer classes for individual modules
      (squares, circles, rounded rectangles, etc.). See the
      ``qrcode.image.styles.moduledrawers`` package.

    - **Embedded images** — place a logo or picture in the centre of the QR code.
      Use error correction level Q or H to maintain scannability.

    Args:
        border: Quiet zone width in modules.
        width: Module grid size.
        box_size: Pixel size per module.
        color_mask: A :class:`QRColorMask` instance controlling colours.
        embedded_image_path: Path to an image file to embed in the centre.
        embedded_image: A Pillow :class:`PIL.Image.Image` instance to embed.
        embedded_image_ratio: Ratio (0–1) of logo width relative to QR code
            width. Default ``0.25``.
        embedded_image_resample: PIL resampling filter for the embedded image.
            Default :attr:`PIL.Image.Resampling.LANCZOS`.
        module_drawer: Drawer instance or alias string for data modules.
        eye_drawer: Drawer instance or alias string for finder pattern eyes.

    Example::

        from qrcode.image.styledpil import StyledPilImage
        from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
        from qrcode.image.styles.colormasks import RadialGradiantColorMask

        img = qrcode.make(
            "data",
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=RadialGradiantColorMask(),
        )
    """

    kind = "PNG"

    needs_processing = True
    color_mask: QRColorMask
    default_drawer_class: type[SquareModuleDrawer] = SquareModuleDrawer  # type: ignore[assignment]

    def __init__(
        self,
        border: int,
        width: int,
        box_size: int,
        *args: Any,
        color_mask: QRColorMask | None = None,
        embedded_image_path: str | None = None,
        embedded_image: Image.Image | None = None,
        embedded_image_ratio: float = 0.25,
        embedded_image_resample: int = Image.Resampling.LANCZOS,
        **kwargs: Any,
    ) -> None:
        """Initialize the styled PIL image factory.

        Args:
            border: Quiet zone width in modules.
            width: Module grid size.
            box_size: Pixel size per module.
            color_mask: Colour mask instance (default: ``SolidFillColorMask``).
            embedded_image_path: Path to an image file to embed.
            embedded_image: Pillow Image to embed directly.
            embedded_image_ratio: Logo width ratio (0–1). Default 0.25.
            embedded_image_resample: PIL resampling filter for logo resize.
            **kwargs: Additional keyword arguments forwarded to parent, including
                ``module_drawer``, ``eye_drawer``, and ``qrcode_modules``.
        """
        self.color_mask = color_mask or SolidFillColorMask()

        # allow kwargs override of explicit parameters (for factory pattern)
        embedded_image_path = kwargs.get("embedded_image_path", embedded_image_path)
        self.embedded_image: Image.Image | None = kwargs.get(
            "embedded_image", embedded_image
        )
        self.embedded_image_ratio: float = kwargs.get(
            "embedded_image_ratio", embedded_image_ratio
        )
        self.embedded_image_resample: int = kwargs.get(
            "embedded_image_resample", embedded_image_resample
        )
        if not self.embedded_image and embedded_image_path:
            self.embedded_image = Image.open(embedded_image_path)

        # the paint_color is the color the module drawer will use to draw upon
        # a canvas. During the color mask process, pixels that are paint_color
        # are replaced by a newly-calculated color.
        self.paint_color: tuple[int, ...] = tuple(0 for _ in self.color_mask.back_color)
        if self.color_mask.has_transparency:
            self.paint_color = (*self.color_mask.back_color[:3], 255)

        super().__init__(border, width, box_size, *args, **kwargs)

    def drawrect(self, row: int, col: int) -> None:
        """Not used — StyledPilImage uses drawrect_context instead."""

    def new_image(self, **kwargs: Any) -> Image.Image:
        """Create a new Pillow image with the correct mode for the colour mask.

        Returns:
            A PIL :class:`PIL.Image.Image` instance (RGB or RGBA).
        """
        mode = (
            "RGBA"
            if (
                self.color_mask.has_transparency
                or (self.embedded_image and "A" in self.embedded_image.getbands())
            )
            else "RGB"
        )
        # This is the background color. Should be white or whiteish
        back_color = self.color_mask.back_color

        return Image.new(mode, (self.pixel_size, self.pixel_size), back_color)

    def init_new_image(self) -> None:
        """Initialize the colour mask and drawers with image references."""
        self.color_mask.initialize(self, self._img)
        super().init_new_image()

    def process(self) -> None:
        """Apply colour mask and draw embedded image (if any)."""
        self.color_mask.apply_mask(self._img)
        if self.embedded_image:
            self.draw_embedded_image()

    def draw_embedded_image(self) -> None:
        """Draw the embedded logo image in the centre of the QR code.

        The logo is resized to ``embedded_image_ratio`` of the total width and
        centred, aligned to module boundaries.
        """
        if not self.embedded_image:
            return
        total_width, _ = self._img.size
        total_width = int(total_width)
        logo_width_ish = int(total_width * self.embedded_image_ratio)
        logo_offset = (
            int((int(total_width / 2) - int(logo_width_ish / 2)) / self.box_size)
            * self.box_size
        )  # round the offset to the nearest module
        logo_position = (logo_offset, logo_offset)
        logo_width = total_width - logo_offset * 2
        region: Image.Image = self.embedded_image
        region = region.resize((logo_width, logo_width), self.embedded_image_resample)
        if "A" in region.getbands():
            self._img.alpha_composite(region, logo_position)
        else:
            self._img.paste(region, logo_position)

    def save(
        self, stream: IO[bytes] | str, kind: str | None = None, **kwargs: Any
    ) -> None:  # type: ignore[override]
        """Save the styled image.

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
