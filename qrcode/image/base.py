from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

from qrcode.image.styles.moduledrawers.base import QRModuleDrawer

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import IO

    from qrcode.main import ActiveWithNeighbors, QRCode


DrawerAliases = dict[str, tuple[type[QRModuleDrawer], dict[str, Any]]]

__all__: list[str] = [
    "BaseImage",
    "BaseImageWithDrawer",
    "DrawerAliases",
]


class BaseImage(abc.ABC):
    """Base class for all QR code image factories (PEP 561 typed).

    Subclasses must implement the abstract methods :meth:`drawrect`,
    :meth:`save`, and :meth:`new_image` to produce a concrete output format.

    **Factory pattern** — A custom factory is created by subclassing this class
    and overriding the three abstract hooks:

    1. ``new_image(**kwargs)`` — instantiate the underlying image object
       (e.g. Pillow ``Image``, SVG root element, pypng writer). Return the
       created instance; it will be stored in ``self._img``.

    2. ``drawrect(row, col)`` — draw a single dark module at grid position
       *(row, col)*. Use :meth:`pixel_box` to get pixel coordinates.

    3. ``save(stream, kind=None)`` — write the finished image to *stream*
       (a file-like object or path).

    Optionally override:

    - ``process()`` — called after all modules are drawn, before saving.
      Useful for post-processing (e.g. combining paths, applying masks).
    - ``init_new_image()`` — called immediately after ``new_image()``,
      before any drawing begins.
    - ``get_image(**kwargs)`` — returns the underlying image object for
      further manipulation by the caller.

    **Class attributes**

    - ``kind`` (str | None): Default output format string, e.g. ``"PNG"``.
    - ``allowed_kinds`` (tuple[str, ...] | None): Allowed formats or ``None``
      to allow any.
    - ``needs_context`` (bool): Set to ``True`` if the factory wants the full
      QR code context during drawing (uses :meth:`drawrect_context`).
    - ``needs_processing`` (bool): Set to ``True`` to trigger a call to
      :meth:`process` before saving.
    - ``needs_drawrect`` (bool): Set to ``False`` if the factory does not use
      individual module drawing (e.g. row-based writers like PyPNG).

    Example — Minimal custom factory::

        class MyImage(BaseImage):
            kind = "MYFMT"

            def new_image(self, **kwargs):
                return []  # placeholder image object

            def drawrect(self, row: int, col: int) -> None:
                self._img.append((row, col))

            def save(self, stream: IO[bytes], kind: str | None = None) -> None:
                for coord in self._img:
                    stream.write(f"module {coord}\\n".encode())
    """

    kind: str | None = None
    allowed_kinds: tuple[str, ...] | None = None
    needs_context = False
    needs_processing = False
    needs_drawrect = True

    def __init__(
        self,
        border: int,
        width: int,
        box_size: int,
        *args: Any,
        qrcode_modules: list[list[bool | None]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the image factory.

        Args:
            border: Quiet zone width in modules.
            width: Module grid size (QR code version-dependent).
            box_size: Pixel size per module.
            qrcode_modules: 2-D boolean grid of QR modules (injected by caller).
            **kwargs: Additional factory-specific keyword arguments forwarded
                to :meth:`new_image`.
        """
        self.border = border
        self.width = width
        self.box_size = box_size
        self.pixel_size = (self.width + self.border * 2) * self.box_size
        self.modules = kwargs.pop("qrcode_modules", qrcode_modules)
        self._img = self.new_image(**kwargs)
        self.init_new_image()

    @abc.abstractmethod
    def drawrect(self, row: int, col: int) -> None:
        """Draw a single dark module at grid position *(row, col)*.

        Args:
            row: Row index (0 = top).
            col: Column index (0 = left).
        """

    def drawrect_context(self, row: int, col: int, qr: QRCode) -> None:
        """Draw a single rectangle of the QR code given the surrounding context.

        Override in subclasses that set ``needs_context = True``. The base
        implementation raises :exc:`NotImplementedError`.

        Args:
            row: Row index.
            col: Column index.
            qr: The parent :class:`~qrcode.main.QRCode` instance providing
                access to neighbouring module state.
        """
        raise NotImplementedError("BaseImage.drawrect_context")  # pragma: no cover

    def process(self) -> None:
        """Post-process the QR code image after all modules are drawn.

        Override in subclasses that set ``needs_processing = True``. The base
        implementation raises :exc:`NotImplementedError`.
        """
        raise NotImplementedError("BaseImage.drawimage")  # pragma: no cover

    @abc.abstractmethod
    def save(self, stream: IO[bytes] | str, kind: str | None = None) -> None:
        """Save the image file.

        Args:
            stream: File-like object (binary mode) or file path string.
            kind: Optional format override. Falls back to ``self.kind`` if
                ``None``.
        """

    def pixel_box(self, row: int, col: int) -> tuple[tuple[int, int], tuple[int, int]]:
        """Return the four pixel coordinates for a single module rect.

        Args:
            row: Row index.
            col: Column index.

        Returns:
            Tuple of two points ``((x0, y0), (x1, y1))`` defining the bounding
            box of the module in pixel space.
        """
        x = (col + self.border) * self.box_size
        y = (row + self.border) * self.box_size
        return (
            (x, y),
            (x + self.box_size - 1, y + self.box_size - 1),
        )

    @abc.abstractmethod
    def new_image(self, **kwargs: Any) -> Any:
        """Build the underlying image object. Subclasses must return the created instance.

        Args:
            **kwargs: Factory-specific keyword arguments (e.g. ``fill_color``,
                ``back_color``).

        Returns:
            The newly created image object (type depends on subclass).
        """

    def init_new_image(self) -> None:  # noqa: B027
        """Called immediately after :meth:`new_image`, before drawing begins.

        Override to perform any setup that requires ``self._img`` to exist.
        The base implementation is a no-op.
        """

    def get_image(self, **kwargs: Any) -> Any:
        """Return the underlying image object for further processing by the caller.

        Returns:
            The image instance created by :meth:`new_image`.
        """
        return self._img

    def check_kind(
        self, kind: str | None, transform: Callable[[str], str] | None = None
    ) -> str:
        """Validate and resolve the output format string.

        Args:
            kind: Format to validate (``None`` means use ``self.kind``).
            transform: Optional callable applied to *kind* before validation.

        Returns:
            The resolved format string.

        Raises:
            ValueError: If *kind* is not in ``self.allowed_kinds`` or is
                unresolved (both *kind* and ``self.kind`` are ``None``).
        """
        if kind is None:
            kind = self.kind
        if kind is None:  # pragma: no cover
            raise ValueError(f"Cannot resolve kind for {type(self).__name__}")
        allowed = (
            not self.allowed_kinds or kind in self.allowed_kinds  # type: ignore[operator]
        )
        if transform:
            kind = transform(kind)
            if not allowed:
                allowed = kind in self.allowed_kinds  # type: ignore[operator]
        if not allowed:
            raise ValueError(f"Cannot set {type(self).__name__} type to {kind}")
        return kind

    def is_eye(self, row: int, col: int) -> bool:
        """Return ``True`` if the module at *(row, col)* belongs to a finder pattern (eye).

        Args:
            row: Row index.
            col: Column index.

        Returns:
            ``True`` when inside one of the three 7×7 finder patterns.
        """
        return (
            (row < 7 and col < 7)
            or (row < 7 and self.width - col < 8)
            or (self.width - row < 8 and col < 7)
        )


class BaseImageWithDrawer(BaseImage):
    """Base image factory with support for pluggable module drawers.

    Subclasses declare a ``default_drawer_class`` and optional
    ``drawer_aliases`` mapping string names to drawer constructors. This enables
    the caller to customise how individual modules (and finder pattern eyes) are
    rendered via the ``module_drawer`` and ``eye_drawer`` parameters on
    :meth:`__init__`.

    Attributes:
        default_drawer_class: Drawer class used for both modules and eyes when
            no explicit drawer is provided.
        drawer_aliases: Mapping of alias strings to ``(drawer_cls, kwargs)``
            tuples for string-based drawer selection.
        module_drawer: The resolved :class:`~qrcode.image.styles.moduledrawers.base.QRModuleDrawer`
            instance used for data modules.
        eye_drawer: The resolved drawer instance used for finder pattern eyes.
    """

    default_drawer_class: type[QRModuleDrawer]
    drawer_aliases: DrawerAliases = {}

    needs_context = True

    module_drawer: QRModuleDrawer
    eye_drawer: QRModuleDrawer

    def __init__(
        self,
        *args: Any,
        module_drawer: QRModuleDrawer | str | None = None,
        eye_drawer: QRModuleDrawer | str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the image factory with pluggable drawers.

        Args:
            *args: Positional arguments forwarded to :class:`BaseImage`.
            module_drawer: Drawer instance or alias string for data modules.
                ``None`` uses ``default_drawer_class``.
            eye_drawer: Drawer instance or alias string for finder pattern eyes.
                ``None`` uses ``default_drawer_class``.
            **kwargs: Additional keyword arguments forwarded to :class:`BaseImage`.
        """
        self.module_drawer = (
            self.get_drawer(module_drawer) or self.get_default_module_drawer()
        )
        # The eye drawer can be overridden by another module drawer as well,
        # but you have to be more careful with these in order to make the QR
        # code still parseable
        self.eye_drawer = self.get_drawer(eye_drawer) or self.get_default_eye_drawer()
        super().__init__(*args, **kwargs)

    def get_default_module_drawer(self) -> QRModuleDrawer:
        """Return a fresh instance of the default module drawer."""
        return self.default_drawer_class()  # type: ignore[misc]

    def get_default_eye_drawer(self) -> QRModuleDrawer:
        """Return a fresh instance of the default eye drawer (same as module by default)."""
        return self.default_drawer_class()  # type: ignore[misc]

    def get_drawer(self, drawer: QRModuleDrawer | str | None) -> QRModuleDrawer | None:
        """Resolve a drawer instance from an existing object or alias string.

        Args:
            drawer: An already-instantiated drawer, an alias string key into
                ``self.drawer_aliases``, or ``None``.

        Returns:
            A :class:`QRModuleDrawer` instance, or ``None`` if *drawer* was
            ``None``.
        """
        if not isinstance(drawer, str):
            return drawer  # type: ignore[return-value]
        drawer_cls, kwargs = self.drawer_aliases[drawer]
        return drawer_cls(**kwargs)

    def init_new_image(self) -> None:
        """Initialize drawers with a reference to this image factory."""
        self.module_drawer.initialize(img=self)
        self.eye_drawer.initialize(img=self)

        super().init_new_image()

    def drawrect_context(self, row: int, col: int, qr: QRCode) -> None:
        """Draw a module using the appropriate drawer (eye or module).

        Args:
            row: Row index.
            col: Column index.
            qr: The parent :class:`~qrcode.main.QRCode` instance.
        """
        box = self.pixel_box(row, col)
        drawer = self.eye_drawer if self.is_eye(row, col) else self.module_drawer
        is_active: bool | ActiveWithNeighbors = (
            qr.active_with_neighbors(row, col)
            if drawer.needs_neighbors
            else bool(qr.modules[row][col])
        )

        drawer.drawrect(box, is_active)
