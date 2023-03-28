from typing import Any

from qrcode import image  # noqa
from qrcode.constants import (  # noqa
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)
from qrcode.main import make  # noqa
from qrcode.main import QRCode


def run_example(
    data: str = "http://www.lincolnloop.com",
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Build an example QR Code and display it.

    There's an even easier way than the code here though: just use the ``make``
    shortcut.
    """
    qr = QRCode[Any](*args, **kwargs)
    qr.add_data(data)

    im = qr.make_image()
    im.show()


if __name__ == "__main__":  # pragma: no cover
    import sys

    run_example(*sys.argv[1:])
