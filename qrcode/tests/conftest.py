import tempfile
from importlib.util import find_spec

import pytest


@pytest.fixture
def dummy_image() -> tempfile.NamedTemporaryFile:
    """
    This function creates a red pixel image with full opacity, saves it as a PNG
    file in a temporary location, and returns the temporary file.
    """
    # Must import here as PIL might be not installed
    from PIL import Image

    # A 1x1 Red Pixel
    dummy_image = Image.new("RGBA", (1, 1), (255, 0, 0, 255))

    # Save the image to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as temp_file:
        dummy_image.save(temp_file.name)
        yield temp_file
