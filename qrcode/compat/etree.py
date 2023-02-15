try:
    import lxml.etree as ET  # type: ignore
except ImportError:
    import xml.etree.ElementTree as ET  # type: ignore

__all__ = ["ET"]
