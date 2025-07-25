try:
    import lxml.etree as ET  # noqa: N812
except ImportError:
    import xml.etree.ElementTree as ET  # noqa: F401
