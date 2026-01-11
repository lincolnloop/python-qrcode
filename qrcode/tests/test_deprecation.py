from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from qrcode.constants import ERROR_CORRECT_H, PIL_AVAILABLE
from qrcode.main import QRCode

if TYPE_CHECKING:
    from tempfile import NamedTemporaryFile


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_moduledrawer_import() -> None:
    """
    Importing a drawer from qrcode.image.styles.moduledrawers is deprecated
    and will raise a DeprecationWarning.

    Removed in v9.0.
    """
    # These module imports are fine to import
    from qrcode.image.styles.moduledrawers import base, pil, svg

    with pytest.warns(
        DeprecationWarning,
        match="Importing 'SquareModuleDrawer' directly from this module is deprecated.",
    ):
        from qrcode.image.styles.moduledrawers import (
            SquareModuleDrawer,
        )


@pytest.mark.skipif(PIL_AVAILABLE, reason="PIL is installed")
def test_moduledrawer_import_pil_not_installed() -> None:
    """
    Importing from qrcode.image.styles.moduledrawers is deprecated, however,
    if PIL is not installed, there will be no (false) warning; it's a simple
    ImportError.

    Removed in v9.0.
    """
    # These module imports are fine to import
    from qrcode.image.styles.moduledrawers import base, svg

    # Importing a backwards compatible module drawer does normally render a
    # DeprecationWarning; however, since PIL is not installed, it will raise an
    # ImportError.
    with pytest.raises(ImportError):
        from qrcode.image.styles.moduledrawers import SquareModuleDrawer


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_make_image_embeded_parameters() -> None:
    """
    Using 'embeded_image_path' or 'embeded_image' parameters with QRCode.make_image()
    is deprecated and will raise a DeprecationWarning.

    Removed in v9.0.
    """

    # Create a QRCode required for embedded images
    qr = QRCode(error_correction=ERROR_CORRECT_H)
    qr.add_data("test")

    # Test with embeded_image_path parameter
    with pytest.warns(
        DeprecationWarning, match="The 'embeded_\\*' parameters are deprecated"
    ):
        qr.make_image(embeded_image_path="dummy_path")

    # Test with embeded_image parameter
    with pytest.warns(
        DeprecationWarning, match="The 'embeded_\\*' parameters are deprecated."
    ):
        qr.make_image(embeded_image="dummy_image")


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL is not installed")
def test_styledpilimage_embeded_parameters(dummy_image: NamedTemporaryFile) -> None:
    """
    Using 'embeded_image_path' or 'embeded_image' parameters with StyledPilImage
    is deprecated and will raise a DeprecationWarning.

    Removed in v9.0.
    """
    from PIL import Image

    from qrcode.image.styledpil import StyledPilImage

    styled_kwargs = {
        "border": 4,
        "width": 21,
        "box_size": 10,
        "qrcode_modules": 1,
    }

    # Test with embeded_image_path parameter
    with pytest.warns(
        DeprecationWarning, match="The 'embeded_\\*' parameters are deprecated."
    ):
        StyledPilImage(embeded_image_path=dummy_image.name, **styled_kwargs)

    # Test with embeded_image parameter
    embedded_img = Image.open(dummy_image.name)

    with pytest.warns(
        DeprecationWarning, match="The 'embeded_\\*' parameters are deprecated."
    ):
        StyledPilImage(embeded_image=embedded_img, **styled_kwargs)
