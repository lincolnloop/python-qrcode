# For backwards compatibility, importing the PIL drawers here.
import contextlib

with contextlib.suppress(ImportError):
    from .pil import (
        CircleModuleDrawer,  # noqa: F401
        GappedCircleModuleDrawer,  # noqa: F401
        GappedSquareModuleDrawer,  # noqa: F401
        HorizontalBarsDrawer,  # noqa: F401
        RoundedModuleDrawer,  # noqa: F401
        SquareModuleDrawer,  # noqa: F401
        VerticalBarsDrawer,  # noqa: F401
    )
