# Try to import PIL in either of the two ways it can be installed.
Image = None
ImageDraw = None

try:
    from PIL import Image, ImageDraw  # type: ignore
except ImportError:  # pragma: no cover
    try:
        import Image  # type: ignore
        import ImageDraw  # type: ignore
    except ImportError:
        pass

__all__ = ["Image", "ImageDraw"]
