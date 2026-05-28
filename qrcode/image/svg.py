from __future__ import annotations

import decimal
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, overload

import qrcode.image.base
from qrcode.compat.etree import ET
from qrcode.image.styles.moduledrawers import svg as svg_drawers

if TYPE_CHECKING:
    from typing import IO

    from qrcode.image.styles.moduledrawers.base import QRModuleDrawer


__all__: list[str] = [
    "SvgFillImage",
    "SvgFragmentImage",
    "SvgImage",
    "SvgPathFillImage",
    "SvgPathImage",
]


class SvgFragmentImage(qrcode.image.base.BaseImageWithDrawer):
    """SVG document fragment image builder for QR codes.

    Creates a QR-code image as a SVG document *fragment* (no XML declaration,
    no standalone ``<svg>`` root with namespace). Use :class:`SvgImage` for a
    complete standalone SVG file.

    Units are expressed in millimetres: a default ``box_size=10`` maps to 1 mm
    per module.

    Attributes:
        kind: Always ``"SVG"``.
        allowed_kinds: ``( "SVG", )``.
        default_drawer_class: :class:`~qrcode.image.styles.moduledrawers.svg.SvgSquareDrawer`.
    """

    _SVG_namespace = "http://www.w3.org/2000/svg"
    kind = "SVG"
    allowed_kinds = ("SVG",)
    default_drawer_class: type[QRModuleDrawer] = svg_drawers.SvgSquareDrawer  # type: ignore[assignment]

    def __init__(
        self,
        border: int,
        width: int,
        box_size: int,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the SVG fragment factory.

        Args:
            border: Quiet zone width in modules.
            width: Module grid size.
            box_size: Pixel size per module (maps to millimetres).
            *args: Additional positional arguments forwarded to parent.
            **kwargs: Keyword arguments including drawer configuration and
                ``qrcode_modules``.
        """
        ET.register_namespace("svg", self._SVG_namespace)
        super().__init__(border, width, box_size, *args, **kwargs)
        # Save the unit size, for example the default box_size of 10 is '1mm'.
        self.unit_size = self.units(self.box_size)

    def drawrect(self, row: int, col: int) -> None:
        """Not used — SvgFragmentImage uses drawrect_context instead."""

    @overload
    def units(self, pixels: int | Decimal, text: Literal[False]) -> Decimal: ...

    @overload
    def units(self, pixels: int | Decimal, text: Literal[True] = True) -> str: ...

    def units(self, pixels: int | Decimal, text: bool = True) -> str | Decimal:
        """Convert pixel count to millimetre units.

        A ``box_size`` of 10 (default) equals 1 mm.

        Args:
            pixels: Number of pixels to convert.
            text: If ``True``, return a string with "mm" suffix. Otherwise
                return the raw :class:`Decimal` value.

        Returns:
            A formatted string like ``"2.500mm"`` or a :class:`Decimal`.
        """
        units = Decimal(pixels) / 10
        if not text:
            return units
        units = units.quantize(Decimal("0.001"))
        context = decimal.Context(traps=[decimal.Inexact])
        try:
            for d in (Decimal("0.01"), Decimal("0.1"), Decimal(0)):
                units = units.quantize(d, context=context)
        except decimal.Inexact:
            pass
        return f"{units}mm"

    def save(self, stream: IO[bytes] | str, kind: str | None = None) -> None:
        """Write the SVG fragment to *stream*.

        Args:
            stream: File-like object (binary mode) or file path string.
            kind: Optional format override (must be ``"SVG"``).
        """
        self.check_kind(kind=kind)
        self._write(stream)

    def to_string(self, **kwargs: Any) -> bytes:
        """Return the SVG fragment as a byte string.

        Args:
            **kwargs: Keyword arguments forwarded to :func:`xml.etree.ElementTree.tostring`.

        Returns:
            Raw XML bytes of the SVG element tree.
        """
        return ET.tostring(self._img, **kwargs)  # type: ignore[no-any-return]

    def new_image(self, **kwargs: Any) -> Any:
        """Create a new SVG root element.

        Returns:
            An :class:`xml.etree.ElementTree.Element` representing the ``<svg>`` root.
        """
        return self._svg(**kwargs)

    def _svg(self, tag: Any = None, version: str = "1.1", **kwargs: Any) -> Any:
        """Build the SVG root element.

        Args:
            tag: Element tag (defaults to namespaced ``"svg"``).
            version: SVG version attribute value.
            **kwargs: Additional attributes on the root element.

        Returns:
            An :class:`xml.etree.ElementTree.Element`.
        """
        if tag is None:
            tag = ET.QName(self._SVG_namespace, "svg")
        dimension = self.units(self.pixel_size)
        return ET.Element(
            tag,
            width=dimension,
            height=dimension,
            version=version,
            **kwargs,
        )

    def _write(self, stream: IO[bytes] | str) -> None:
        """Write the element tree without an XML declaration.

        Args:
            stream: File-like object or path string.
        """
        ET.ElementTree(self._img).write(stream, xml_declaration=False)


class SvgImage(SvgFragmentImage):
    """Standalone SVG image builder for QR codes.

    Produces a complete SVG document with XML declaration and proper namespace
    on the root ``<svg>`` element. Supports optional background colour fill.

    Attributes:
        background: Background colour (``None`` = transparent). Override to
            ``"white"`` via :class:`SvgFillImage`.
        drawer_aliases: Pre-configured drawer shortcuts — ``"circle"``,
            ``"gapped-circle"``, ``"gapped-square"``.
    """

    background: str | None = None
    drawer_aliases: qrcode.image.base.DrawerAliases = {
        "circle": (svg_drawers.SvgCircleDrawer, {}),
        "gapped-circle": (svg_drawers.SvgCircleDrawer, {"size_ratio": Decimal("0.8")}),
        "gapped-square": (svg_drawers.SvgSquareDrawer, {"size_ratio": Decimal("0.8")}),
    }

    def _svg(self, tag: str = "svg", **kwargs: Any) -> Any:  # type: ignore[override]
        """Build a standalone SVG root element with namespace.

        Args:
            tag: Tag name (no namespace prefix needed).
            **kwargs: Additional attributes forwarded to parent ``_svg``.

        Returns:
            An :class:`xml.etree.ElementTree.Element`.
        """
        svg = super()._svg(tag=tag, **kwargs)
        svg.set("xmlns", self._SVG_namespace)
        if self.background:
            svg.append(
                ET.Element(
                    "rect",
                    fill=self.background,
                    x="0",
                    y="0",
                    width="100%",
                    height="100%",
                )
            )
        return svg

    def _write(self, stream: IO[bytes] | str) -> None:
        """Write the element tree with XML declaration and UTF-8 encoding.

        Args:
            stream: File-like object or path string.
        """
        ET.ElementTree(self._img).write(stream, encoding="UTF-8", xml_declaration=True)


class SvgPathImage(SvgImage):
    """SVG image builder that combines all modules into a single ``<path>`` element.

    This reduces whitespace between individual QR points and produces smaller
    output files compared to per-module ``<rect>`` elements.

    Attributes:
        needs_processing: ``True`` — triggers :meth:`process` which assembles
            the final path data string.
        default_drawer_class: :class:`~qrcode.image.styles.moduledrawers.svg.SvgPathSquareDrawer`.
        drawer_aliases: Pre-configured path-based drawer shortcuts.
    """

    QR_PATH_STYLE: dict[str, str] = {
        "fill": "#000000",
        "fill-opacity": "1",
        "fill-rule": "nonzero",
        "stroke": "none",
    }

    needs_processing = True
    path: Any | None = None
    default_drawer_class: type[QRModuleDrawer] = svg_drawers.SvgPathSquareDrawer  # type: ignore[assignment]
    drawer_aliases: qrcode.image.base.DrawerAliases = {
        "circle": (svg_drawers.SvgPathCircleDrawer, {}),
        "gapped-circle": (
            svg_drawers.SvgPathCircleDrawer,
            {"size_ratio": Decimal("0.8")},
        ),
        "gapped-square": (
            svg_drawers.SvgPathSquareDrawer,
            {"size_ratio": Decimal("0.8")},
        ),
    }

    def __init__(
        self,
        border: int,
        width: int,
        box_size: int,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the SVG path factory.

        Args:
            border: Quiet zone width in modules.
            width: Module grid size.
            box_size: Pixel size per module.
            *args: Additional positional arguments forwarded to parent.
            **kwargs: Keyword arguments including drawer configuration.
        """
        self._subpaths: list[str] = []
        super().__init__(border, width, box_size, *args, **kwargs)

    def _svg(self, viewBox: str | None = None, **kwargs: Any) -> Any:  # type: ignore[override]
        """Build SVG root with a viewBox attribute.

        Args:
            viewBox: ViewBox string (auto-computed if ``None``).
            **kwargs: Additional attributes forwarded to parent.

        Returns:
            An :class:`xml.etree.ElementTree.Element`.
        """
        if viewBox is None:
            dimension = self.units(self.pixel_size, text=False)
            viewBox = f"0 0 {dimension} {dimension}"
        return super()._svg(viewBox=viewBox, **kwargs)

    def process(self) -> None:
        """Assemble collected sub-paths into a single ``<path>`` element."""
        # Store the path just in case someone wants to use it again or in some
        # unique way.
        self.path = ET.Element(
            ET.QName("path"),
            d="".join(self._subpaths),
            **self.QR_PATH_STYLE,
        )
        self._subpaths = []
        self._img.append(self.path)


class SvgFillImage(SvgImage):
    """An :class:`SvgImage` that fills the background to white."""

    background = "white"


class SvgPathFillImage(SvgPathImage):
    """An :class:`SvgPathImage` that fills the background to white."""

    background = "white"
