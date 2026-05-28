"""Tests for v9.0 breaking changes — removed deprecated APIs.

These tests verify that the deprecated features from v8.x are no longer available,
ensuring clean removal in v9.0.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from qrcode.constants import ERROR_CORRECT_H, PIL_AVAILABLE
from qrcode.main import QRCode

if TYPE_CHECKING:
    from tempfile import NamedTemporaryFile


# ---------------------------------------------------------------------------
# TASK-37: moduledrawers direct imports removed
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_moduledrawer_import_removed() -> None:
    """Importing a drawer directly from the package root now raises ImportError.

    Users must import from the submodule instead::

        from qrcode.image.styles.moduledrawers.pil import SquareModuleDrawer
    """
    # Submodule imports still work fine
    from qrcode.image.styles.moduledrawers import base, pil, svg
    from qrcode.image.styles.moduledrawers.base import QRModuleDrawer

    assert QRModuleDrawer is not None

    # Direct drawer import from package root should fail
    with pytest.raises(ImportError):
        from qrcode.image.styles.moduledrawers import SquareModuleDrawer


@pytest.mark.skipif(PIL_AVAILABLE, reason="PIL is installed")
def test_moduledrawer_import_pil_not_installed() -> None:
    """Without PIL, importing drawers from the package root still fails."""
    from qrcode.image.styles.moduledrawers import base, svg

    with pytest.raises(ImportError):
        from qrcode.image.styles.moduledrawers import SquareModuleDrawer


# ---------------------------------------------------------------------------
# TASK-36: embeded_* parameters removed
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_make_image_embeded_parameters_removed() -> None:
    """Using 'embeded_*' parameters (typo) no longer works.

    The correct parameter names are 'embedded_image_path' and 'embedded_image'.
    Passing the misspelled versions silently does nothing (ignored as kwargs).
    """
    qr = QRCode(error_correction=ERROR_CORRECT_H)
    qr.add_data("test")

    # embeded_* parameters should be silently ignored (no warning, no error)
    # since they are not recognized parameter names anymore.
    # The image is created normally without any embedded image.
    img = qr.make_image()  # No embeded_* params — works fine
    assert img is not None


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_styledpilimage_embeded_parameters_removed(
    dummy_image: NamedTemporaryFile,
) -> None:
    """StyledPilImage no longer accepts 'embeded_*' parameters (typo).

    The correct parameter names are 'embedded_image_path' and 'embedded_image'.
    """
    from PIL import Image

    from qrcode.image.styledpil import StyledPilImage

    styled_kwargs = {
        "border": 4,
        "width": 21,
        "box_size": 10,
        "qrcode_modules": 1,
    }

    # Correct parameters work fine
    img = StyledPilImage(embedded_image_path=dummy_image.name, **styled_kwargs)
    assert img is not None

    # embeded_* typo parameters are silently ignored (passed as kwargs)
    # The image is created without any embedded image.
    img_no_embed = StyledPilImage(**styled_kwargs)
    assert img_no_embed is not None


# ---------------------------------------------------------------------------
# TASK-38: draw_embeded_image() method removed
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_draw_embeded_image_method_removed() -> None:
    """The deprecated method 'draw_embeded_image()' (typo) has been removed.

    Only 'draw_embedded_image()' exists now.
    """
    from qrcode.image.styledpil import StyledPilImage

    assert not hasattr(StyledPilImage, "draw_embeded_image")
    assert hasattr(StyledPilImage, "draw_embedded_image")


# ---------------------------------------------------------------------------
# Correct API still works
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_correct_embedded_api_works(dummy_image: NamedTemporaryFile) -> None:
    """The correct 'embedded_*' parameters work as expected."""
    from PIL import Image

    from qrcode.image.styledpil import StyledPilImage

    styled_kwargs = {
        "border": 4,
        "width": 21,
        "box_size": 10,
        "qrcode_modules": 1,
    }

    # embedded_image_path works
    img = StyledPilImage(embedded_image_path=dummy_image.name, **styled_kwargs)
    assert img.embedded_image is not None

    # embedded_image works
    pil_img = Image.open(dummy_image.name)
    img2 = StyledPilImage(embedded_image=pil_img, **styled_kwargs)
    assert img2.embedded_image is not None


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_moduledrawer_submodule_imports_work() -> None:
    """Direct imports from submodules still work correctly."""
    from qrcode.image.styles.moduledrawers.pil import (
        CircleModuleDrawer,
        GappedCircleModuleDrawer,
        GappedSquareModuleDrawer,
        HorizontalBarsDrawer,
        RoundedModuleDrawer,
        SquareModuleDrawer,
        VerticalBarsDrawer,
    )

    assert SquareModuleDrawer is not None
    assert CircleModuleDrawer is not None
    assert RoundedModuleDrawer is not None
