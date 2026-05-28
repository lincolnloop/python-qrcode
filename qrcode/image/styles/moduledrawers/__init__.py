"""Module drawers for styled QR codes.

Import drawers directly from the submodules:

    from qrcode.image.styles.moduledrawers.base import QRModuleDrawer
    from qrcode.image.styles.moduledrawers.pil import SquareModuleDrawer
    from qrcode.image.styles.moduledrawers.svg import SvgSquareModuleDrawer

Direct imports of PIL/SVG drawers from this package (e.g.
``from qrcode.image.styles.moduledrawers import SquareModuleDrawer``) are no
longer supported as of v9.0. Only :class:`~qrcode.image.styles.moduledrawers.base.QRModuleDrawer`
is re-exported here for convenience, since it has no circular dependencies.
"""

from __future__ import annotations

from .base import QRModuleDrawer

__all__: list[str] = [
    "QRModuleDrawer",
]
