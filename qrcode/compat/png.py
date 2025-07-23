import contextlib

# Try to import png library.
PngWriter = None

with contextlib.suppress(ImportError):
    from png import Writer as PngWriter  # noqa: F401
