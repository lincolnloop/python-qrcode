from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qrcode.image.base import BaseImage
    from qrcode.main import ActiveWithNeighbors


__all__: list[str] = [
    "QRModuleDrawer",
]


class QRModuleDrawer(abc.ABC):
    """QR module drawer — renders individual modules onto an image.

    Subclasses implement :meth:`drawrect` to draw a single module within the
    given *box* coordinates. If ``needs_neighbors`` is set to ``True``, the
    method also receives a ``neighbors`` argument describing the 3×3
    neighbourhood around the module.

    An optional :meth:`initialize` hook lets subclasses access image-level
    attributes (size, colours, drawing context).

    For visual examples see ``doc/module_drawers.png``.
    """

    needs_neighbors: bool = False

    def __init__(self, **kwargs: Any) -> None:  # noqa: B027
        """Initialize the drawer.

        Args:
            **kwargs: Subclass-specific keyword arguments.
        """

    def initialize(self, img: BaseImage) -> None:
        """Set up internal state from the parent image object.

        Args:
            img: The containing image instance (PIL, SVG, etc.).
        """
        self.img = img  # type: ignore[misc]

    @abc.abstractmethod
    def drawrect(self, box: Any, is_active: bool | ActiveWithNeighbors) -> None: ...
