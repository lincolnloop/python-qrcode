"""
Module for lazy importing of PIL drawers with a deprecation warning.

Currently, importing a PIL drawer from this module is allowed for backwards
compatibility but will raise a DeprecationWarning.

This will be removed in v9.0.
"""

import warnings

from qrcode.constants import PIL_AVAILABLE


def __getattr__(name):
    """Lazy import with deprecation warning for PIL drawers."""
    # List of PIL drawer names that should trigger deprecation warnings
    pil_drawers = {
        "CircleModuleDrawer",
        "GappedCircleModuleDrawer",
        "GappedSquareModuleDrawer",
        "HorizontalBarsDrawer",
        "RoundedModuleDrawer",
        "SquareModuleDrawer",
        "VerticalBarsDrawer",
    }

    if name in pil_drawers:
        # Only render a warning if PIL is actually installed. Otherwise it would
        # raise an ImportError directly, which is fine.
        if PIL_AVAILABLE:
            warnings.warn(
                f"Importing '{name}' directly from this module is deprecated."
                f"Please use 'from qrcode.image.styles.moduledrawers.pil import {name}' "
                f"instead. This backwards compatibility import will be removed in v9.0.",
                DeprecationWarning,
                stacklevel=2,
            )

        # Import and return the drawer from the pil module
        from . import pil  # noqa: PLC0415

        return getattr(pil, name)

    # For any other attribute, raise AttributeError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
