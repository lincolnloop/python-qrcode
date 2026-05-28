"""Compatibility shim for pypng — provides PngWriter if available."""

from __future__ import annotations

# Try to import png library.
PngWriter: type | None = None

try:
    from png import Writer as PngWriter
except ImportError:
    pass

__all__: list[str] = [
    "PngWriter",
]
