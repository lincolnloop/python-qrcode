"""QR code specific exceptions."""


class DataOverflowError(Exception):
    """Raised when data exceeds the capacity of the selected QR version and EC level.

    This occurs during :meth:`~qrcode.main.QRCode.make` (with ``fit=False``) or
    internally in :func:`qrcode.util.create_data` when the encoded bit length is
    larger than the available data capacity for the current configuration.

    Example::

        qr = qrcode.QRCode(version=1)  # version 1 holds ~20 bytes
        qr.add_data("this string is way too long for version 1")
        qr.make(fit=False)  # raises DataOverflowError
    """


__all__: list[str] = [
    "DataOverflowError",
]
