from __future__ import annotations

import abc
from decimal import Decimal
from typing import TYPE_CHECKING, Any, NamedTuple

from qrcode.compat.etree import ET
from qrcode.image.styles.moduledrawers.base import QRModuleDrawer

if TYPE_CHECKING:
    from qrcode.image.svg import SvgFragmentImage, SvgPathImage
    from qrcode.main import ActiveWithNeighbors


__all__: list[str] = [
    "ANTIALIASING_FACTOR",
    "BaseSvgQRModuleDrawer",
    "Coords",
    "SvgCircleDrawer",
    "SvgPathCircleDrawer",
    "SvgPathQRModuleDrawer",
    "SvgPathSquareDrawer",
    "SvgQRModuleDrawer",
    "SvgSquareDrawer",
]

ANTIALIASING_FACTOR = 4


class Coords(NamedTuple):
    x0: Decimal
    y0: Decimal
    x1: Decimal
    y1: Decimal
    xh: Decimal
    yh: Decimal


class BaseSvgQRModuleDrawer(QRModuleDrawer):
    """Base SVG module drawer with size ratio and coordinate helpers."""

    img: SvgFragmentImage

    def __init__(self, *, size_ratio: Decimal = Decimal(1), **kwargs: Any) -> None:
        """Initialize the base SVG drawer.

        Args:
            size_ratio: Ratio (0–1) of module size relative to cell size.
                ``1`` fills the entire cell; smaller values create gaps.
            **kwargs: Additional keyword arguments forwarded to parent.
        """
        super().__init__(**kwargs)
        self.size_ratio = size_ratio

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Compute box dimensions from the parent image."""
        super().initialize(*args, **kwargs)
        self.box_delta = (1 - self.size_ratio) * self.img.box_size / 2
        self.box_size = Decimal(self.img.box_size) * self.size_ratio
        self.box_half = self.box_size / 2

    def coords(self, box: Any) -> Coords:
        """Convert a module box to SVG coordinates.

        Args:
            box: Module position — ``((row, col), ...)`` or equivalent.

        Returns:
            :class:`Coords` named tuple with computed positions.
        """
        row, col = box[0]
        x = row + self.box_delta
        y = col + self.box_delta

        return Coords(
            x,
            y,
            x + self.box_size,
            y + self.box_size,
            x + self.box_half,
            y + self.box_half,
        )


class SvgQRModuleDrawer(BaseSvgQRModuleDrawer):
    """SVG drawer that appends individual ``<rect>``/``<circle>`` elements."""

    tag: str = "rect"

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the SVG element drawer."""
        super().initialize(*args, **kwargs)

    def drawrect(self, box: Any, is_active: bool | ActiveWithNeighbors) -> None:
        """Draw a single module as an SVG element.

        Args:
            box: Module position coordinates.
            is_active: Whether the module should be drawn (``True`` = dark).
                For drawers with ``needs_neighbors=True``, this may also be
                an :class:`~qrcode.main.ActiveWithNeighbors` instance.
        """
        if not is_active:
            return
        self.img._img.append(self.el(box))  # type: ignore[attr-defined]

    @abc.abstractmethod
    def el(self, box: Any) -> Any: ...


class SvgSquareDrawer(SvgQRModuleDrawer):
    """Draw modules as SVG ``<rect>`` elements."""

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Pre-compute the unit size string for rectangles."""
        super().initialize(*args, **kwargs)
        self.unit_size = self.img.units(self.box_size)

    def el(self, box: Any) -> Any:
        """Create a ``<rect>`` element for one module.

        Args:
            box: Module position coordinates.

        Returns:
            An :class:`xml.etree.ElementTree.Element` representing the rect.
        """
        coords = self.coords(box)
        return ET.Element(
            self.tag,
            x=self.img.units(coords.x0),
            y=self.img.units(coords.y0),
            width=self.unit_size,
            height=self.unit_size,
        )


class SvgCircleDrawer(SvgQRModuleDrawer):
    """Draw modules as SVG ``<circle>`` elements."""

    tag: str = "circle"

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Pre-compute the radius string for circles."""
        super().initialize(*args, **kwargs)
        self.radius = self.img.units(self.box_half)

    def el(self, box: Any) -> Any:
        """Create a ``<circle>`` element for one module.

        Args:
            box: Module position coordinates.

        Returns:
            An :class:`xml.etree.ElementTree.Element` representing the circle.
        """
        coords = self.coords(box)
        return ET.Element(
            self.tag,
            cx=self.img.units(coords.xh),
            cy=self.img.units(coords.yh),
            r=self.radius,
        )


class SvgPathQRModuleDrawer(BaseSvgQRModuleDrawer):
    """SVG drawer that accumulates path data for a combined ``<path>`` element."""

    img: SvgPathImage

    def drawrect(self, box: Any, is_active: bool | ActiveWithNeighbors) -> None:
        """Append path sub-data for one module.

        Args:
            box: Module position coordinates.
            is_active: Whether the module should be drawn (``True`` = dark).
                For drawers with ``needs_neighbors=True``, this may also be
                an :class:`~qrcode.main.ActiveWithNeighbors` instance.
        """
        if not is_active:
            return
        self.img._subpaths.append(self.subpath(box))  # type: ignore[attr-defined]

    @abc.abstractmethod
    def subpath(self, box: Any) -> str: ...


class SvgPathSquareDrawer(SvgPathQRModuleDrawer):
    """Generate path data for square modules."""

    def subpath(self, box: Any) -> str:
        """Return SVG path commands for one square module.

        Args:
            box: Module position coordinates.

        Returns:
            A path string like ``M0,0H1V1H0z``.
        """
        coords = self.coords(box)
        x0 = self.img.units(coords.x0, text=False)
        y0 = self.img.units(coords.y0, text=False)
        x1 = self.img.units(coords.x1, text=False)
        y1 = self.img.units(coords.y1, text=False)

        return f"M{x0},{y0}H{x1}V{y1}H{x0}z"


class SvgPathCircleDrawer(SvgPathQRModuleDrawer):
    """Generate path data for circular modules."""

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the circle path drawer."""
        super().initialize(*args, **kwargs)

    def subpath(self, box: Any) -> str:
        """Return SVG path commands for one circular module.

        Uses two arc segments to approximate a circle.

        Args:
            box: Module position coordinates.

        Returns:
            A path string with ``A`` (arc) commands forming a circle.
        """
        coords = self.coords(box)
        x0 = self.img.units(coords.x0, text=False)
        yh = self.img.units(coords.yh, text=False)
        h = self.img.units(self.box_half - self.box_delta, text=False)
        x1 = self.img.units(coords.x1, text=False)

        # rx,ry is the centerpoint of the arc
        # 1? is the x-axis-rotation
        # 2? is the large-arc-flag
        # 3? is the sweep flag
        # x,y is the point the arc is drawn to

        return f"M{x0},{yh}A{h},{h} 0 0 0 {x1},{yh}A{h},{h} 0 0 0 {x0},{yh}z"
