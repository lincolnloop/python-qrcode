from qrcode import image
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)
from qrcode.main import QRCode, make

__all__ = [
    "ERROR_CORRECT_H",
    "ERROR_CORRECT_L",
    "ERROR_CORRECT_M",
    "ERROR_CORRECT_Q",
    "QRCode",
    "image",
    "make",
    "run_example",
]


def run_example(data="http://www.lincolnloop.com", *args, **kwargs):
    """
    Build an example QR Code and display it.

    There's an even easier way than the code here though: just use the ``make``
    shortcut.
    """
    qr = QRCode(*args, **kwargs)
    qr.add_data(data)

    im = qr.make_image()
    im.show()


if __name__ == "__main__":  # pragma: no cover
    import sys

    run_example(*sys.argv[1:])
