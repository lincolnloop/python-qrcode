from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PIL import Image, ImageDraw

from qrcode.image.styles.moduledrawers.base import QRModuleDrawer
from qrcode.main import ActiveWithNeighbors

if TYPE_CHECKING:
    from qrcode.image.styledpil import StyledPilImage


__all__: list[str] = [
    "BoxCoords",
    "CircleModuleDrawer",
    "GappedCircleModuleDrawer",
    "GappedSquareModuleDrawer",
    "HorizontalBarsDrawer",
    "RoundedModuleDrawer",
    "SquareModuleDrawer",
    "StyledPilQRModuleDrawer",
    "VerticalBarsDrawer",
]

# When drawing antialiased things, make them bigger and then shrink them down
# to size after the geometry has been drawn.
ANTIALIASING_FACTOR = 4


class BoxCoords:
    """Type alias for module box coordinates.

    A box is represented as ``((x0, y0), (x1, y1))`` where ``(x0, y0)`` is
    the top-left corner and ``(x1, y1)`` is the bottom-right corner.
    """


Box = tuple[tuple[int, int], tuple[int, int]]


class StyledPilQRModuleDrawer(QRModuleDrawer):
    """Base class for PIL-based module drawers used by :class:`StyledPilImage`.

    Subclasses draw individual QR modules onto a PIL image. The colour that is
    drawn should be the equivalent of black in the current colour space; the
    specified :class:`~qrcode.image.styles.colormasks.QRColorMask` will handle
    adding colours afterwards.

    Attributes:
        img: Reference to the parent :class:`StyledPilImage` instance, set
            during :meth:`initialize`.
    """

    img: StyledPilImage


class SquareModuleDrawer(StyledPilQRModuleDrawer):
    """Draw modules as simple filled squares.

    The default drawer — each active module is rendered as a solid square with
    no gaps between adjacent modules.
    """

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Set up the PIL ``ImageDraw`` context.

        Args:
            *args: Passed to parent :meth:`~QRModuleDrawer.initialize`.
            **kwargs: Additional keyword arguments (unused).
        """
        super().initialize(*args, **kwargs)
        self.imgDraw = ImageDraw.Draw(self.img._img)  # type: ignore[attr-defined]

    def drawrect(self, box: Box, is_active: bool | ActiveWithNeighbors) -> None:
        """Draw a single module as a square.

        Args:
            box: Coordinate tuple ``((x0, y0), (x1, y1))`` defining the
                bounding rectangle for this module.
            is_active: ``True`` if the module should be drawn (foreground).
        """
        if is_active:
            self.imgDraw.rectangle(box, fill=self.img.paint_color)  # type: ignore[attr-defined]


class GappedSquareModuleDrawer(StyledPilQRModuleDrawer):
    """Draw modules as non-contiguous squares with gaps between them.

    The *size_ratio* controls how wide the drawn square is relative to the
    available space (``1.0`` = full size, ``0.8`` = 20 % gap).

    Args:
        size_ratio: Ratio of module width to available cell width (default
            ``0.8``, producing a 20 % gap around each square).
    """

    def __init__(self, size_ratio: float = 0.8) -> None:
        """Initialize with the desired module-to-cell ratio.

        Args:
            size_ratio: How large each drawn square is relative to its cell.
                Values in ``(0, 1]``; ``1.0`` gives contiguous squares.
        """
        self.size_ratio = size_ratio

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Set up drawing context and compute the gap delta.

        Args:
            *args: Passed to parent :meth:`~QRModuleDrawer.initialize`.
            **kwargs: Additional keyword arguments (unused).
        """
        super().initialize(*args, **kwargs)
        self.imgDraw = ImageDraw.Draw(self.img._img)  # type: ignore[attr-defined]
        self.delta = (1 - self.size_ratio) * self.img.box_size / 2  # type: ignore[attr-defined]

    def drawrect(self, box: Box, is_active: bool | ActiveWithNeighbors) -> None:
        """Draw a gapped square module.

        Args:
            box: Coordinate tuple ``((x0, y0), (x1, y1))`` for the full cell.
            is_active: ``True`` if the module should be drawn.
        """
        if is_active:
            smaller_box: Box = (  # type: ignore[assignment]
                box[0][0] + self.delta,  # type: ignore[arg-type]
                box[0][1] + self.delta,  # type: ignore[arg-type]
                box[1][0] - self.delta,  # type: ignore[arg-type]
                box[1][1] - self.delta,  # type: ignore[arg-type]
            )
            self.imgDraw.rectangle(smaller_box, fill=self.img.paint_color)  # type: ignore[attr-defined]


class CircleModuleDrawer(StyledPilQRModuleDrawer):
    """Draw modules as filled circles.

    Each active module is rendered as an antialiased circle that fills the
    available cell space. A pre-rendered circle template is created during
    :meth:`initialize` and blitted for every active module.
    """

    circle: Image.Image | None = None

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Create an antialiased circle template.

        A larger circle is drawn at ``ANTIALIASING_FACTOR``× resolution and
        then downscaled with Lanczos filtering for smooth edges.

        Args:
            *args: Passed to parent :meth:`~QRModuleDrawer.initialize`.
            **kwargs: Additional keyword arguments (unused).
        """
        super().initialize(*args, **kwargs)
        box_size = self.img.box_size  # type: ignore[attr-defined]
        fake_size = box_size * ANTIALIASING_FACTOR
        self.circle = Image.new(
            self.img.mode,  # type: ignore[attr-defined]
            (fake_size, fake_size),
            self.img.color_mask.back_color,  # type: ignore[attr-defined]
        )
        ImageDraw.Draw(self.circle).ellipse(
            (0, 0, fake_size, fake_size),
            fill=self.img.paint_color,  # type: ignore[attr-defined]
        )
        self.circle = self.circle.resize((box_size, box_size), Image.Resampling.LANCZOS)

    def drawrect(self, box: Box, is_active: bool | ActiveWithNeighbors) -> None:
        """Blit the pre-rendered circle onto the module cell.

        Args:
            box: Coordinate tuple ``((x0, y0), (x1, y1))`` for the cell.
            is_active: ``True`` if the module should be drawn.
        """
        if is_active and self.circle is not None:
            self.img._img.paste(self.circle, (box[0][0], box[0][1]))  # type: ignore[attr-defined]


class GappedCircleModuleDrawer(StyledPilQRModuleDrawer):
    """Draw modules as non-contiguous circles with gaps.

    Similar to :class:`CircleModuleDrawer` but the rendered circle is smaller
    than the cell, leaving visible gaps between neighbouring modules.

    Args:
        size_ratio: Ratio of circle diameter to available cell width (default
            ``0.9``). Smaller values produce larger gaps.
    """

    circle: Image.Image | None = None

    def __init__(self, size_ratio: float = 0.9) -> None:
        """Initialize with the desired circle-to-cell ratio.

        Args:
            size_ratio: How large each drawn circle is relative to its cell.
                Values in ``(0, 1]``.
        """
        self.size_ratio = size_ratio

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Create a downscaled antialiased circle template.

        Args:
            *args: Passed to parent :meth:`~QRModuleDrawer.initialize`.
            **kwargs: Additional keyword arguments (unused).
        """
        super().initialize(*args, **kwargs)
        box_size = self.img.box_size  # type: ignore[attr-defined]
        fake_size = box_size * ANTIALIASING_FACTOR
        self.circle = Image.new(
            self.img.mode,  # type: ignore[attr-defined]
            (fake_size, fake_size),
            self.img.color_mask.back_color,  # type: ignore[attr-defined]
        )
        ImageDraw.Draw(self.circle).ellipse(
            (0, 0, fake_size, fake_size),
            fill=self.img.paint_color,  # type: ignore[attr-defined]
        )
        smaller_size = int(self.size_ratio * box_size)
        self.circle = self.circle.resize(
            (smaller_size, smaller_size), Image.Resampling.LANCZOS
        )

    def drawrect(self, box: Box, is_active: bool | ActiveWithNeighbors) -> None:
        """Blit the gapped circle template onto the module cell.

        Args:
            box: Coordinate tuple ``((x0, y0), (x1, y1))`` for the cell.
                The circle is pasted at the top-left corner; smaller circles
                will leave gaps on all sides.
            is_active: ``True`` if the module should be drawn.
        """
        if is_active and self.circle is not None:
            self.img._img.paste(self.circle, (box[0][0], box[0][1]))  # type: ignore[attr-defined]


class RoundedModuleDrawer(StyledPilQRModuleDrawer):
    """Draw modules with rounded corners.

    Contiguous active modules share edges so the result looks like a single
    shape with smooth outer corners and straight shared edges. The
    *radius_ratio* controls how pronounced the rounding is (``1.0`` = fully
    circular for isolated modules, ``0.0`` = sharp squares).

    This drawer requires neighbour information (:attr:`needs_neighbors` =
    ``True``) so it can decide which corners to round based on adjacent
    active modules.

    Args:
        radius_ratio: Corner rounding intensity in ``(0, 1]`` (default ``1``).
            A value of ``1`` produces a circle for an isolated module; a
            value of ``0`` reverts to sharp squares.
    """

    needs_neighbors = True
    radius_ratio: float
    corner_width: int
    SQUARE: Image.Image
    NW_ROUND: Image.Image
    NE_ROUND: Image.Image
    SE_ROUND: Image.Image
    SW_ROUND: Image.Image

    def __init__(self, radius_ratio: float = 1) -> None:
        """Initialize with the desired corner rounding intensity.

        Args:
            radius_ratio: How much to round each corner (``0`` = square,
                ``1`` = maximally rounded / circular).
        """
        self.radius_ratio = radius_ratio

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Pre-render the four corner templates and a flat-square template.

        Args:
            *args: Passed to parent :meth:`~QRModuleDrawer.initialize`.
            **kwargs: Additional keyword arguments (unused).
        """
        super().initialize(*args, **kwargs)
        self.corner_width = int(self.img.box_size / 2)  # type: ignore[attr-defined]
        self.setup_corners()

    def setup_corners(self) -> None:
        """Build the four rounded-corner images and a flat square."""
        mode = self.img.mode  # type: ignore[attr-defined]
        back_color = self.img.color_mask.back_color  # type: ignore[attr-defined]
        front_color = self.img.paint_color  # type: ignore[attr-defined]
        self.SQUARE = Image.new(
            mode, (self.corner_width, self.corner_width), front_color
        )

        fake_width = self.corner_width * ANTIALIASING_FACTOR
        radius = self.radius_ratio * fake_width
        diameter = radius * 2
        base = Image.new(
            mode, (fake_width, fake_width), back_color
        )  # make something 4x bigger for antialiasing
        base_draw = ImageDraw.Draw(base)
        base_draw.ellipse((0, 0, diameter, diameter), fill=front_color)
        base_draw.rectangle((radius, 0, fake_width, fake_width), fill=front_color)
        base_draw.rectangle((0, radius, fake_width, fake_width), fill=front_color)
        self.NW_ROUND = base.resize(
            (self.corner_width, self.corner_width), Image.Resampling.LANCZOS
        )
        self.SW_ROUND = self.NW_ROUND.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.SE_ROUND = self.NW_ROUND.transpose(Image.Transpose.ROTATE_180)
        self.NE_ROUND = self.NW_ROUND.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    def drawrect(
        self, box: list[list[int]], is_active: bool | ActiveWithNeighbors
    ) -> None:
        """Draw a module with selectively rounded corners.

        Corners are rounded only when the corresponding neighbouring module
        is inactive (i.e. the edge is an outer boundary).

        Args:
            box: Coordinate list ``[[x0, y0], [x1, y1]]`` for the cell.
            is_active: Named tuple with boolean flags ``N``, ``S``, ``E``,
                ``W`` indicating whether each neighbour is active.
        """
        if not is_active:
            return
        assert isinstance(is_active, ActiveWithNeighbors)
        # find rounded edges
        nw_rounded = not is_active.W and not is_active.N
        ne_rounded = not is_active.N and not is_active.E
        se_rounded = not is_active.E and not is_active.S
        sw_rounded = not is_active.S and not is_active.W

        nw = self.NW_ROUND if nw_rounded else self.SQUARE
        ne = self.NE_ROUND if ne_rounded else self.SQUARE
        se = self.SE_ROUND if se_rounded else self.SQUARE
        sw = self.SW_ROUND if sw_rounded else self.SQUARE
        self.img._img.paste(nw, (box[0][0], box[0][1]))  # type: ignore[attr-defined]
        self.img._img.paste(ne, (box[0][0] + self.corner_width, box[0][1]))  # type: ignore[attr-defined]
        self.img._img.paste(  # type: ignore[attr-defined]
            se, (box[0][0] + self.corner_width, box[0][1] + self.corner_width)
        )
        self.img._img.paste(  # type: ignore[attr-defined]
            sw, (box[0][0], box[0][1] + self.corner_width)
        )


class VerticalBarsDrawer(StyledPilQRModuleDrawer):
    """Draw vertically contiguous modules as rounded bars.

    Neighbouring active modules in the same column are merged into a single
    vertical bar with rounded top/bottom caps. The *horizontal_shrink*
    parameter controls how narrow the bars are relative to the cell width,
    creating gaps between adjacent columns.

    Requires neighbour information (:attr:`needs_neighbors` = ``True``).

    Args:
        horizontal_shrink: Width of each bar as a fraction of the cell width
            (default ``0.8``, producing 20 % gaps between columns).
    """

    needs_neighbors = True
    horizontal_shrink: float
    half_height: int
    delta: int
    SQUARE: Image.Image
    ROUND_TOP: Image.Image
    ROUND_BOTTOM: Image.Image

    def __init__(self, horizontal_shrink: float = 0.8) -> None:
        """Initialize with the desired bar width ratio.

        Args:
            horizontal_shrink: How wide each vertical bar is relative to its
                cell (``0 < value <= 1``). Smaller values = wider gaps between
                columns.
        """
        self.horizontal_shrink = horizontal_shrink

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Pre-render the bar cap templates.

        Args:
            *args: Passed to parent :meth:`~QRModuleDrawer.initialize`.
            **kwargs: Additional keyword arguments (unused).
        """
        super().initialize(*args, **kwargs)
        self.half_height = int(self.img.box_size / 2)  # type: ignore[attr-defined]
        self.delta = int((1 - self.horizontal_shrink) * self.half_height)
        self.setup_edges()

    def setup_edges(self) -> None:
        """Build rounded top/bottom cap images and a flat rectangle."""
        mode = self.img.mode  # type: ignore[attr-defined]
        back_color = self.img.color_mask.back_color  # type: ignore[attr-defined]
        front_color = self.img.paint_color  # type: ignore[attr-defined]

        height = self.half_height
        width = height * 2
        shrunken_width = int(width * self.horizontal_shrink)
        self.SQUARE = Image.new(mode, (shrunken_width, height), front_color)

        fake_width = width * ANTIALIASING_FACTOR
        fake_height = height * ANTIALIASING_FACTOR
        base = Image.new(
            mode, (fake_width, fake_height), back_color
        )  # make something 4x bigger for antialiasing
        base_draw = ImageDraw.Draw(base)
        base_draw.ellipse((0, 0, fake_width, fake_height * 2), fill=front_color)

        self.ROUND_TOP = base.resize((shrunken_width, height), Image.Resampling.LANCZOS)
        self.ROUND_BOTTOM = self.ROUND_TOP.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    def drawrect(self, box: Any, is_active: bool | ActiveWithNeighbors) -> None:
        """Draw a vertical bar segment with rounded caps at boundaries.

        The top cap is rounded when the northern neighbour is inactive; the
        bottom cap is rounded when the southern neighbour is inactive.

        Args:
            box: Coordinate tuple for the module cell (type depends on PIL).
            is_active: Named tuple with ``N`` and ``S`` boolean flags
                indicating whether the north/south neighbours are active.
        """
        if is_active:
            assert isinstance(is_active, ActiveWithNeighbors)
            # find rounded edges
            top_rounded = not is_active.N
            bottom_rounded = not is_active.S

            top = self.ROUND_TOP if top_rounded else self.SQUARE
            bottom = self.ROUND_BOTTOM if bottom_rounded else self.SQUARE
            self.img._img.paste(top, (box[0][0] + self.delta, box[0][1]))  # type: ignore[attr-defined]
            self.img._img.paste(  # type: ignore[attr-defined]
                bottom, (box[0][0] + self.delta, box[0][1] + self.half_height)
            )


class HorizontalBarsDrawer(StyledPilQRModuleDrawer):
    """Draw horizontally contiguous modules as rounded bars.

    Neighbouring active modules in the same row are merged into a single
    horizontal bar with rounded left/right caps. The *vertical_shrink*
    parameter controls how tall the bars are relative to the cell height,
    creating gaps between adjacent rows.

    Requires neighbour information (:attr:`needs_neighbors` = ``True``).

    Args:
        vertical_shrink: Height of each bar as a fraction of the cell height
            (default ``0.8``, producing 20 % gaps between rows).
    """

    needs_neighbors = True
    vertical_shrink: float
    half_width: int
    delta: int
    SQUARE: Image.Image
    ROUND_LEFT: Image.Image
    ROUND_RIGHT: Image.Image

    def __init__(self, vertical_shrink: float = 0.8) -> None:
        """Initialize with the desired bar height ratio.

        Args:
            vertical_shrink: How tall each horizontal bar is relative to its
                cell (``0 < value <= 1``). Smaller values = wider gaps between
                rows.
        """
        self.vertical_shrink = vertical_shrink

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Pre-render the bar cap templates.

        Args:
            *args: Passed to parent :meth:`~QRModuleDrawer.initialize`.
            **kwargs: Additional keyword arguments (unused).
        """
        super().initialize(*args, **kwargs)
        self.half_width = int(self.img.box_size / 2)  # type: ignore[attr-defined]
        self.delta = int((1 - self.vertical_shrink) * self.half_width)
        self.setup_edges()

    def setup_edges(self) -> None:
        """Build rounded left/right cap images and a flat rectangle."""
        mode = self.img.mode  # type: ignore[attr-defined]
        back_color = self.img.color_mask.back_color  # type: ignore[attr-defined]
        front_color = self.img.paint_color  # type: ignore[attr-defined]

        width = self.half_width
        height = width * 2
        shrunken_height = int(height * self.vertical_shrink)
        self.SQUARE = Image.new(mode, (width, shrunken_height), front_color)

        fake_width = width * ANTIALIASING_FACTOR
        fake_height = height * ANTIALIASING_FACTOR
        base = Image.new(
            mode, (fake_width, fake_height), back_color
        )  # make something 4x bigger for antialiasing
        base_draw = ImageDraw.Draw(base)
        base_draw.ellipse((0, 0, fake_width * 2, fake_height), fill=front_color)

        self.ROUND_LEFT = base.resize(
            (width, shrunken_height), Image.Resampling.LANCZOS
        )
        self.ROUND_RIGHT = self.ROUND_LEFT.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    def drawrect(self, box: Any, is_active: bool | ActiveWithNeighbors) -> None:
        """Draw a horizontal bar segment with rounded caps at boundaries.

        The left cap is rounded when the western neighbour is inactive; the
        right cap is rounded when the eastern neighbour is inactive.

        Args:
            box: Coordinate tuple for the module cell (type depends on PIL).
            is_active: Named tuple with ``W`` and ``E`` boolean flags
                indicating whether the west/east neighbours are active.
        """
        if is_active:
            assert isinstance(is_active, ActiveWithNeighbors)
            # find rounded edges
            left_rounded = not is_active.W
            right_rounded = not is_active.E

            left = self.ROUND_LEFT if left_rounded else self.SQUARE
            right = self.ROUND_RIGHT if right_rounded else self.SQUARE
            self.img._img.paste(left, (box[0][0], box[0][1] + self.delta))  # type: ignore[attr-defined]
            self.img._img.paste(  # type: ignore[attr-defined]
                right, (box[0][0] + self.half_width, box[0][1] + self.delta)
            )
