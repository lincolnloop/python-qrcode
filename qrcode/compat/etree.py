"""Compatibility shim for ElementTree — prefers lxml if available."""

from __future__ import annotations

try:
    import lxml.etree as ET  # noqa: N812
except ImportError:
    import xml.etree.ElementTree as ET

__all__: list[str] = [
    "ET",
]
