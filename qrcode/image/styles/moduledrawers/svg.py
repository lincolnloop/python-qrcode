import abc
from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple

from qrcode.image.styles.moduledrawers.base import QRModuleDrawer
from qrcode.compat.etree import ET

if TYPE_CHECKING:
    from qrcode.image.svg import SvgFragmentImage, SvgPathImage

ANTIALIASING_FACTOR = 4


class Coords(NamedTuple):
    x0: Decimal
    y0: Decimal
    x1: Decimal
    y1: Decimal
    xh: Decimal
    yh: Decimal


class BaseSvgQRModuleDrawer(QRModuleDrawer):
    img: "SvgFragmentImage"

    def __init__(self, *, size_ratio: Decimal = Decimal(1), **kwargs):
        self.size_ratio = size_ratio

    def initialize(self, *args, **kwargs) -> None:
        super().initialize(*args, **kwargs)
        self.box_delta = (1 - self.size_ratio) * self.img.box_size / 2
        self.box_size = Decimal(self.img.box_size) * self.size_ratio
        self.box_half = self.box_size / 2

    def coords(self, box) -> Coords:
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
    tag = "rect"

    def initialize(self, *args, **kwargs) -> None:
        super().initialize(*args, **kwargs)
        self.tag_qname = ET.QName(self.img._SVG_namespace, self.tag)

    def drawrect(self, box, is_active: bool):
        if not is_active:
            return
        self.img._img.append(self.el(box))

    @abc.abstractmethod
    def el(self, box): ...


class SvgSquareDrawer(SvgQRModuleDrawer):
    def initialize(self, *args, **kwargs) -> None:
        super().initialize(*args, **kwargs)
        self.unit_size = self.img.units(self.box_size)

    def el(self, box):
        coords = self.coords(box)
        return ET.Element(
            self.tag_qname,  # type: ignore
            x=self.img.units(coords.x0),
            y=self.img.units(coords.y0),
            width=self.unit_size,
            height=self.unit_size,
        )


class SvgCircleDrawer(SvgQRModuleDrawer):
    tag = "circle"

    def initialize(self, *args, **kwargs) -> None:
        super().initialize(*args, **kwargs)
        self.radius = self.img.units(self.box_half)

    def el(self, box):
        coords = self.coords(box)
        return ET.Element(
            self.tag_qname,  # type: ignore
            cx=self.img.units(coords.xh),
            cy=self.img.units(coords.yh),
            r=self.radius,
        )


class SvgPathQRModuleDrawer(BaseSvgQRModuleDrawer):
    img: "SvgPathImage"

    def drawrect(self, box, is_active: bool):
        if not is_active:
            return
        self.img._subpaths.append(self.subpath(box))

    @abc.abstractmethod
    def subpath(self, box) -> str: ...


class SvgPathSquareDrawer(SvgPathQRModuleDrawer):
    def subpath(self, box) -> str:
        coords = self.coords(box)
        x0 = self.img.units(coords.x0, text=False)
        y0 = self.img.units(coords.y0, text=False)
        x1 = self.img.units(coords.x1, text=False)
        y1 = self.img.units(coords.y1, text=False)

        return f"M{x0},{y0}H{x1}V{y1}H{x0}z"


class SvgPathCircleDrawer(SvgPathQRModuleDrawer):
    def initialize(self, *args, **kwargs) -> None:
        super().initialize(*args, **kwargs)

    def subpath(self, box) -> str:
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


class SvgRoundedModuleDrawer(SvgPathQRModuleDrawer):
    """
    Draws the modules with all 90 degree corners replaced with rounded edges.

    radius_ratio determines the radius of the rounded edges - a value of 1
    means that an isolated module will be drawn as a circle, while a value of 0
    means that the radius of the rounded edge will be 0 (and thus back to 90
    degrees again).
    """
    needs_neighbors = True

    def __init__(self, radius_ratio: Decimal = Decimal(1), **kwargs):
        super().__init__(**kwargs)
        self.radius_ratio = radius_ratio

    def initialize(self, *args, **kwargs) -> None:
        super().initialize(*args, **kwargs)
        self.corner_radius = self.box_half * self.radius_ratio

    def drawrect(self, box, is_active):
        if not is_active:
            return
        
        # Check if is_active has neighbor information (ActiveWithNeighbors object)
        if hasattr(is_active, 'N'):
            # Neighbor information is available
            self.img._subpaths.append(self.subpath(box, is_active))
        else:
            # No neighbor information available, draw a square with all corners rounded
            self.img._subpaths.append(self.subpath_all_rounded(box))

    def subpath_all_rounded(self, box) -> str:
        """Draw a module with all corners rounded."""
        coords = self.coords(box)
        x0 = self.img.units(coords.x0, text=False)
        y0 = self.img.units(coords.y0, text=False)
        x1 = self.img.units(coords.x1, text=False)
        y1 = self.img.units(coords.y1, text=False)
        r = self.img.units(self.corner_radius, text=False)
        
        # Build the path with all corners rounded
        path = []
        
        # Start at top-left after the rounded part
        path.append(f"M{x0 + r},{y0}")
        
        # Top edge to top-right corner
        path.append(f"H{x1 - r}")
        # Top-right rounded corner
        path.append(f"A{r},{r} 0 0 1 {x1},{y0 + r}")
        
        # Right edge to bottom-right corner
        path.append(f"V{y1 - r}")
        # Bottom-right rounded corner
        path.append(f"A{r},{r} 0 0 1 {x1 - r},{y1}")
        
        # Bottom edge to bottom-left corner
        path.append(f"H{x0 + r}")
        # Bottom-left rounded corner
        path.append(f"A{r},{r} 0 0 1 {x0},{y1 - r}")
        
        # Left edge to top-left corner
        path.append(f"V{y0 + r}")
        # Top-left rounded corner
        path.append(f"A{r},{r} 0 0 1 {x0 + r},{y0}")
        
        # Close the path
        path.append("z")
        
        return "".join(path)

    def subpath(self, box, is_active) -> str:
        """Draw a module with corners rounded based on neighbor information."""
        # Determine which corners should be rounded
        nw_rounded = not is_active.W and not is_active.N
        ne_rounded = not is_active.N and not is_active.E
        se_rounded = not is_active.E and not is_active.S
        sw_rounded = not is_active.S and not is_active.W
        
        coords = self.coords(box)
        x0 = self.img.units(coords.x0, text=False)
        y0 = self.img.units(coords.y0, text=False)
        x1 = self.img.units(coords.x1, text=False)
        y1 = self.img.units(coords.y1, text=False)
        r = self.img.units(self.corner_radius, text=False)
        
        # Build the path
        path = []
        
        # Start at top-left and move clockwise
        if nw_rounded:
            # Start at top-left corner, after the rounded part
            path.append(f"M{x0 + r},{y0}")
        else:
            # Start at the top-left corner
            path.append(f"M{x0},{y0}")
        
        # Top edge to top-right corner
        if ne_rounded:
            path.append(f"H{x1 - r}")
            # Top-right rounded corner
            path.append(f"A{r},{r} 0 0 1 {x1},{y0 + r}")
        else:
            path.append(f"H{x1}")
        
        # Right edge to bottom-right corner
        if se_rounded:
            path.append(f"V{y1 - r}")
            # Bottom-right rounded corner
            path.append(f"A{r},{r} 0 0 1 {x1 - r},{y1}")
        else:
            path.append(f"V{y1}")
        
        # Bottom edge to bottom-left corner
        if sw_rounded:
            path.append(f"H{x0 + r}")
            # Bottom-left rounded corner
            path.append(f"A{r},{r} 0 0 1 {x0},{y1 - r}")
        else:
            path.append(f"H{x0}")
        
        # Left edge back to start
        if nw_rounded:
            path.append(f"V{y0 + r}")
            # Top-left rounded corner
            path.append(f"A{r},{r} 0 0 1 {x0 + r},{y0}")
        else:
            path.append(f"V{y0}")
        
        # Close the path
        path.append("z")
        
        return "".join(path)
