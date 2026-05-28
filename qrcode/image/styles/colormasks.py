from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from qrcode.image.styledpil import StyledPilImage


__all__: list[str] = [
    "HorizontalGradiantColorMask",
    "ImageColorMask",
    "QRColorMask",
    "RadialGradiantColorMask",
    "SolidFillColorMask",
    "SquareGradiantColorMask",
    "VerticalGradiantColorMask",
]


class QRColorMask:
    """Base class for coloring QR code modules.

    By the time ``apply_mask`` is called, the :class:`QRModuleDrawer` of the
    :class:`~qrcode.image.styledpil.StyledPilImage` will have drawn all of the
    modules on the canvas (the color of these modules will be mostly black,
    although antialiasing may result in gradients). In the base class,
    ``apply_mask`` is implemented such that the background color will remain,
    but the foreground pixels will be replaced by a color determined by a call
    to :meth:`get_fg_pixel`. There is additional calculation done to preserve
    the gradient artifacts of antialiasing.

    All :class:`QRColorMask` objects should be careful about RGB vs RGBA color
    spaces.

    For examples of what these look like, see ``doc/color_masks.png``.
    """

    back_color: tuple[int, ...] = (255, 255, 255)
    has_transparency: bool = False
    paint_color: tuple[int, ...]

    def __init__(self) -> None:
        """Initialize the color mask with default white background."""

    def initialize(self, styledPilImage: StyledPilImage, image: Image.Image) -> None:
        """Initialize the mask with image-specific data.

        Args:
            styledPilImage: The parent :class:`StyledPilImage` instance.
            image: The PIL ``Image`` being drawn onto.
        """
        self.paint_color = styledPilImage.paint_color

    def apply_mask(self, image: Image.Image, use_cache: bool = False) -> None:
        """Apply the color mask to the rendered QR code image.

        Iterates over every pixel and replaces foreground pixels with colors
        from :meth:`get_fg_pixel` while preserving background pixels at
        :attr:`back_color`. Antialiasing gradients are interpolated between
        the background and foreground colors.

        Args:
            image: The PIL ``Image`` to apply the mask onto.
            use_cache: If ``True``, cache computed foreground colors for
                repeated pixel values (speeds up masks with few distinct
                colors).
        """
        width, height = image.size
        pixels = image.load()
        if pixels is None:
            return
        fg_color_cache: dict[tuple[int, ...], tuple[int, ...]] = {}
        for x in range(width):
            for y in range(height):
                current_color: tuple[int, ...] = tuple(pixels[x, y])  # type: ignore[arg-type]
                if current_color == self.back_color:
                    continue
                if use_cache and fg_color_cache and current_color in fg_color_cache:
                    pixels[x, y] = fg_color_cache[current_color]
                    continue
                norm = self.extrap_color(
                    self.back_color, self.paint_color, current_color
                )
                if norm is not None:
                    new_color = self.interp_color(
                        self.get_bg_pixel(image, x, y),
                        self.get_fg_pixel(image, x, y),
                        norm,
                    )
                    pixels[x, y] = new_color

                    if use_cache:
                        fg_color_cache[current_color] = new_color
                else:
                    pixels[x, y] = self.get_bg_pixel(image, x, y)

    def get_fg_pixel(self, image: Image.Image, x: int, y: int) -> tuple[int, ...]:
        """Return the foreground color for pixel at ``(x, y)``.

        Args:
            image: The PIL ``Image`` being colored.
            x: X coordinate of the pixel.
            y: Y coordinate of the pixel.

        Returns:
            An RGB or RGBA tuple representing the desired color.

        Raises:
            NotImplementedError: Must be overridden by subclasses.
        """
        raise NotImplementedError("QRColorMask.get_fg_pixel")

    def get_bg_pixel(self, image: Image.Image, x: int, y: int) -> tuple[int, ...]:
        """Return the background color for pixel at ``(x, y)``.

        Default returns :attr:`back_color`. Override for spatially varying
        backgrounds.

        Args:
            image: The PIL ``Image`` being colored.
            x: X coordinate of the pixel.
            y: Y coordinate of the pixel.

        Returns:
            An RGB or RGBA tuple representing the background color.
        """
        return self.back_color

    # ------------------------------------------------------------------
    # Color interpolation helpers (public API — used by subclasses)
    # ------------------------------------------------------------------

    def interp_num(self, n1: int, n2: int, norm: float) -> int:
        """Interpolate between two integer values.

        Args:
            n1: Start value.
            n2: End value.
            norm: Normalised position in ``[0, 1]``.

        Returns:
            Interpolated integer value.
        """
        return int(n2 * norm + n1 * (1 - norm))

    def interp_color(
        self, col1: tuple[int, ...], col2: tuple[int, ...], norm: float
    ) -> tuple[int, ...]:
        """Interpolate between two colour tuples.

        Args:
            col1: Start RGB(A) tuple.
            col2: End RGB(A) tuple.
            norm: Normalised position in ``[0, 1]``.

        Returns:
            Interpolated RGB(A) tuple.
        """
        return tuple(self.interp_num(col1[i], col2[i], norm) for i in range(len(col1)))

    def extrap_num(self, n1: int, n2: int, interped_num: int) -> float | None:
        """Find the interpolation coefficient that produced *interped_num*.

        Args:
            n1: Start value.
            n2: End value.
            interped_num: The interpolated result to reverse-engineer.

        Returns:
            Normalised coefficient in ``[0, 1]``, or ``None`` when
            *n1* == *n2*.
        """
        if n2 == n1:
            return None
        return (interped_num - n1) / (n2 - n1)

    def extrap_color(
        self,
        col1: tuple[int, ...],
        col2: tuple[int, ...],
        interped_color: tuple[int, ...],
    ) -> float | None:
        """Find the interpolation coefficient between two colour tuples.

        Args:
            col1: Start RGB(A) tuple.
            col2: End RGB(A) tuple.
            interped_color: The interpolated result to reverse-engineer.

        Returns:
            Average normalised coefficient across channels, or ``None`` if
            no channel can be extrapolated.
        """
        normed: list[float] = []
        for c1, c2, ci in zip(col1, col2, interped_color, strict=False):
            extrap = self.extrap_num(c1, c2, ci)
            if extrap is not None:
                normed.append(extrap)
        if not normed:
            return None
        return sum(normed) / len(normed)


# ---------------------------------------------------------------------------
# Concrete colour masks
# ---------------------------------------------------------------------------


class SolidFillColorMask(QRColorMask):
    """Fill the foreground with a single solid color.

    The simplest mask — replaces every active module pixel with *front_color*
    and leaves background pixels at *back_color*.

    Args:
        back_color: RGB or RGBA tuple for the quiet zone (default white).
        front_color: RGB or RGBA tuple for active modules (default black).
    """

    def __init__(
        self,
        back_color: tuple[int, ...] = (255, 255, 255),
        front_color: tuple[int, ...] = (0, 0, 0),
    ) -> None:
        """Initialize with solid foreground and background colors.

        Args:
            back_color: Background RGB(A) tuple.
            front_color: Foreground RGB(A) tuple for active modules.
        """
        self.back_color = back_color
        self.front_color = front_color
        self.has_transparency = len(self.back_color) == 4

    def apply_mask(self, image: Image.Image, use_cache: bool = False) -> None:
        """Apply a solid fill mask (ignores *use_cache* for speed).

        If both colors are the default black-on-white the method returns
        early because the drawer already produced that output.

        Args:
            image: The PIL ``Image`` to recolour.
            use_cache: Unused; kept for signature compatibility with
                :meth:`~QRColorMask.apply_mask`.
        """
        if self.back_color == (255, 255, 255) and self.front_color == (0, 0, 0):
            # Optimization: the image is already drawn by QRModuleDrawer in
            # black and white, so if these are also our mask colors we don't
            # need to do anything. This is much faster than actually applying a
            # mask.
            return

        image.paste(
            Image.composite(
                Image.new("RGB", image.size, self.front_color),  # type: ignore[arg-type]
                Image.new("RGB", image.size, self.back_color),  # type: ignore[arg-type]
                image.convert("L").point(lambda p: 255 if p < 128 else 0),
            )
        )

    def get_fg_pixel(self, image: Image.Image, x: int, y: int) -> tuple[int, ...]:
        """Return the solid foreground color.

        Args:
            image: Unused.
            x: Unused.
            y: Unused.

        Returns:
            :attr:`front_color`.
        """
        return self.front_color


class RadialGradiantColorMask(QRColorMask):
    """Radial gradient from the centre to the edge of the QR code.

    The foreground pixels are coloured with a smooth radial gradient that
    transitions from *center_color* at the middle of the image to
    *edge_color* at the corners.

    Args:
        back_color: Background RGB(A) tuple (default white).
        center_color: Colour at the centre of the QR code (default black).
        edge_color: Colour at the outer edge (default blue ``(0, 0, 255)``).
    """

    def __init__(
        self,
        back_color: tuple[int, ...] = (255, 255, 255),
        center_color: tuple[int, ...] = (0, 0, 0),
        edge_color: tuple[int, ...] = (0, 0, 255),
    ) -> None:
        """Initialize the radial gradient mask.

        Args:
            back_color: Background color for quiet zone.
            center_color: Color at the centre of the QR code.
            edge_color: Color at the outer corners.
        """
        self.back_color = back_color
        self.center_color = center_color
        self.edge_color = edge_color
        self.has_transparency = len(self.back_color) == 4

    def get_fg_pixel(self, image: Image.Image, x: int, y: int) -> tuple[int, ...]:
        """Return the gradient color at ``(x, y)``.

        Args:
            image: The PIL ``Image`` (used only for size).
            x: X coordinate of the pixel.
            y: Y coordinate of the pixel.

        Returns:
            Interpolated RGB(A) tuple between centre and edge colors.
        """
        width, _ = image.size
        normedDistanceToCenter = math.sqrt(
            (x - width / 2) ** 2 + (y - width / 2) ** 2
        ) / (math.sqrt(2) * width / 2)
        return self.interp_color(
            self.center_color, self.edge_color, normedDistanceToCenter
        )


class SquareGradiantColorMask(QRColorMask):
    """Square gradient from the centre to the edge of the QR code.

    Similar to :class:`RadialGradiantColorMask` but uses Chebyshev distance
    (max of |dx|, |dy|), producing square isoclines instead of circular ones.

    Args:
        back_color: Background RGB(A) tuple (default white).
        center_color: Colour at the centre (default black).
        edge_color: Colour at the outer edge (default blue ``(0, 0, 255)``).
    """

    def __init__(
        self,
        back_color: tuple[int, ...] = (255, 255, 255),
        center_color: tuple[int, ...] = (0, 0, 0),
        edge_color: tuple[int, ...] = (0, 0, 255),
    ) -> None:
        """Initialize the square gradient mask.

        Args:
            back_color: Background color for quiet zone.
            center_color: Color at the centre of the QR code.
            edge_color: Color at the outer corners.
        """
        self.back_color = back_color
        self.center_color = center_color
        self.edge_color = edge_color
        self.has_transparency = len(self.back_color) == 4

    def get_fg_pixel(self, image: Image.Image, x: int, y: int) -> tuple[int, ...]:
        """Return the square-gradient color at ``(x, y)``.

        Args:
            image: The PIL ``Image`` (used only for size).
            x: X coordinate of the pixel.
            y: Y coordinate of the pixel.

        Returns:
            Interpolated RGB(A) tuple based on Chebyshev distance from centre.
        """
        width, _ = image.size
        normedDistanceToCenter = max(abs(x - width / 2), abs(y - width / 2)) / (
            width / 2
        )
        return self.interp_color(
            self.center_color, self.edge_color, normedDistanceToCenter
        )


class HorizontalGradiantColorMask(QRColorMask):
    """Horizontal gradient sweeping from left to right.

    Foreground pixels transition smoothly from *left_color* on the left edge
    of the image to *right_color* on the right edge.

    Args:
        back_color: Background RGB(A) tuple (default white).
        left_color: Colour at the left edge (default black).
        right_color: Colour at the right edge (default blue ``(0, 0, 255)``).
    """

    def __init__(
        self,
        back_color: tuple[int, ...] = (255, 255, 255),
        left_color: tuple[int, ...] = (0, 0, 0),
        right_color: tuple[int, ...] = (0, 0, 255),
    ) -> None:
        """Initialize the horizontal gradient mask.

        Args:
            back_color: Background color for quiet zone.
            left_color: Color at the left edge.
            right_color: Color at the right edge.
        """
        self.back_color = back_color
        self.left_color = left_color
        self.right_color = right_color
        self.has_transparency = len(self.back_color) == 4

    def get_fg_pixel(self, image: Image.Image, x: int, y: int) -> tuple[int, ...]:
        """Return the horizontal-gradient color at ``(x, y)``.

        Args:
            image: The PIL ``Image`` (used only for width).
            x: X coordinate of the pixel.
            y: Y coordinate (unused; gradient is purely horizontal).

        Returns:
            Interpolated RGB(A) tuple based on horizontal position.
        """
        width, _ = image.size
        return self.interp_color(self.left_color, self.right_color, x / width)


class VerticalGradiantColorMask(QRColorMask):
    """Vertical gradient sweeping from top to bottom.

    Foreground pixels transition smoothly from *top_color* at the top edge
    of the image to *bottom_color* at the bottom edge.

    Args:
        back_color: Background RGB(A) tuple (default white).
        top_color: Colour at the top edge (default black).
        bottom_color: Colour at the bottom edge (default blue ``(0, 0, 255)``).
    """

    def __init__(
        self,
        back_color: tuple[int, ...] = (255, 255, 255),
        top_color: tuple[int, ...] = (0, 0, 0),
        bottom_color: tuple[int, ...] = (0, 0, 255),
    ) -> None:
        """Initialize the vertical gradient mask.

        Args:
            back_color: Background color for quiet zone.
            top_color: Color at the top edge.
            bottom_color: Color at the bottom edge.
        """
        self.back_color = back_color
        self.top_color = top_color
        self.bottom_color = bottom_color
        self.has_transparency = len(self.back_color) == 4

    def get_fg_pixel(self, image: Image.Image, x: int, y: int) -> tuple[int, ...]:
        """Return the vertical-gradient color at ``(x, y)``.

        Args:
            image: The PIL ``Image`` (used only for width).
            x: X coordinate (unused; gradient is purely vertical).
            y: Y coordinate of the pixel.

        Returns:
            Interpolated RGB(A) tuple based on vertical position.
        """
        width, _ = image.size
        return self.interp_color(self.top_color, self.bottom_color, y / width)


class ImageColorMask(QRColorMask):
    """Use an external image as the foreground colour source.

    Each active module pixel is recoloured with the corresponding pixel from
    a separate image (loaded either by path or passed directly). The source
    image is automatically resized to match the QR code dimensions during
    :meth:`initialize`.

    Args:
        back_color: Background RGB(A) tuple (default white).
        color_mask_path: Filesystem path to the colour mask image. Ignored if
            *color_mask_image* is provided.
        color_mask_image: A PIL ``Image`` object used directly as the colour
            source. Takes precedence over *color_mask_path*.
    """

    def __init__(
        self,
        back_color: tuple[int, ...] = (255, 255, 255),
        color_mask_path: str | None = None,
        color_mask_image: Image.Image | None = None,
    ) -> None:
        """Initialize the image-based colour mask.

        Args:
            back_color: Background color for quiet zone.
            color_mask_path: Path to load the mask image from (if no direct
                image is provided).
            color_mask_image: PIL ``Image`` object used directly as the mask.
        """
        self.back_color = back_color
        if color_mask_image:
            self.color_img = color_mask_image
        elif color_mask_path is not None:
            self.color_img = Image.open(color_mask_path)
        else:
            raise ValueError(
                "Either color_mask_image or color_mask_path must be provided"
            )

        self.has_transparency = len(self.back_color) == 4

    def initialize(self, styledPilImage: StyledPilImage, image: Image.Image) -> None:
        """Resize the mask image to match the QR code dimensions.

        Args:
            styledPilImage: The parent :class:`StyledPilImage` instance.
            image: The target PIL ``Image`` whose size is used for resizing.
        """
        self.paint_color = styledPilImage.paint_color
        self.color_img = self.color_img.resize(image.size)

    def get_fg_pixel(self, image: Image.Image, x: int, y: int) -> tuple[int, ...]:
        """Return the mask-image color at ``(x, y)``.

        Args:
            image: Unused (the mask is already resized).
            x: X coordinate of the pixel.
            y: Y coordinate of the pixel.

        Returns:
            RGB(A) tuple from the resized colour mask image.
        """
        return self.color_img.getpixel((x, y))  # type: ignore[return-value]
