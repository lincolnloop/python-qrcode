# Try to import png library.
PngWriter = None

try:
    from png import Writer as PngWriter  # noqa: F401
except ImportError:
    pass
