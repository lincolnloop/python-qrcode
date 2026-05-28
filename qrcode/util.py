from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

from qrcode import LUT, base, exceptions

if TYPE_CHECKING:
    from collections.abc import Callable, Generator


# ---------------------------------------------------------------------------
# Module documentation
# ---------------------------------------------------------------------------
"""QR code data encoding utilities (ISO/IEC 18004).

This module provides the core functions for encoding data into QR code byte
streams, including encoding modes (numeric, alphanumeric, 8-bit byte), a bit
buffer (:class:`BitBuffer`), data chunks (:class:`QRData`), mask evaluation
penalty scoring (:func:`lost_point`, levels 1-4), BCH type information encoding,
and optimal data chunk splitting.

Constants:
    MODE_NUMBER (int): Numeric mode identifier (value 0).
    MODE_ALPHA_NUM (int): Alphanumeric mode identifier (value 1).
    MODE_8BIT_BYTE (int): Byte mode identifier (value 2).
    MODE_KANJI (int): Kanji mode identifier (value 3, not implemented).
    ALPHA_NUM (bytes): Character set for alphanumeric encoding.
    PAD0 / PAD1 (int): Alternating padding byte values (0xEC, 0x11).
"""

__all__: list[str] = [
    "ALPHA_NUM",
    "BIT_LIMIT_TABLE",
    "MODE_8BIT_BYTE",
    "MODE_ALPHA_NUM",
    "MODE_KANJI",
    "MODE_NUMBER",
    "MODE_SIZE_LARGE",
    "MODE_SIZE_MEDIUM",
    "MODE_SIZE_SMALL",
    "NUMBER_LENGTH",
    "PAD0",
    "PAD1",
    "PATTERN_POSITION_TABLE",
    "BCH_digit",
    "BCH_type_info",
    "BCH_type_number",
    "BitBuffer",
    "QRData",
    "check_version",
    "create_bytes",
    "create_data",
    "length_in_bits",
    "lost_point",
    "mask_func",
    "mode_sizes_for_version",
    "optimal_data_chunks",
    "optimal_mode",
    "pattern_position",
    "to_bytestring",
]

# QR encoding modes.
MODE_NUMBER = 1 << 0
MODE_ALPHA_NUM = 1 << 1
MODE_8BIT_BYTE = 1 << 2
MODE_KANJI = 1 << 3

# Encoding mode sizes.
MODE_SIZE_SMALL: dict[int, int] = {
    MODE_NUMBER: 10,
    MODE_ALPHA_NUM: 9,
    MODE_8BIT_BYTE: 8,
    MODE_KANJI: 8,
}
MODE_SIZE_MEDIUM: dict[int, int] = {
    MODE_NUMBER: 12,
    MODE_ALPHA_NUM: 11,
    MODE_8BIT_BYTE: 16,
    MODE_KANJI: 10,
}
MODE_SIZE_LARGE: dict[int, int] = {
    MODE_NUMBER: 14,
    MODE_ALPHA_NUM: 13,
    MODE_8BIT_BYTE: 16,
    MODE_KANJI: 12,
}

ALPHA_NUM = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
RE_ALPHA_NUM = re.compile(b"^[" + re.escape(ALPHA_NUM) + rb"]*\Z")

# The number of bits for numeric delimited data lengths.
NUMBER_LENGTH: dict[int, int] = {3: 10, 2: 7, 1: 4}

PATTERN_POSITION_TABLE: list[list[int]] = [
    [],
    [6, 18],
    [6, 22],
    [6, 26],
    [6, 30],
    [6, 34],
    [6, 22, 38],
    [6, 24, 42],
    [6, 26, 46],
    [6, 28, 50],
    [6, 30, 54],
    [6, 32, 58],
    [6, 34, 62],
    [6, 26, 46, 66],
    [6, 26, 48, 70],
    [6, 26, 50, 74],
    [6, 30, 54, 78],
    [6, 30, 56, 82],
    [6, 30, 58, 86],
    [6, 34, 62, 90],
    [6, 28, 50, 72, 94],
    [6, 26, 50, 74, 98],
    [6, 30, 54, 78, 102],
    [6, 28, 54, 80, 106],
    [6, 32, 58, 84, 110],
    [6, 30, 58, 86, 114],
    [6, 34, 62, 90, 118],
    [6, 26, 50, 74, 98, 122],
    [6, 30, 54, 78, 102, 126],
    [6, 26, 52, 78, 104, 130],
    [6, 30, 56, 82, 108, 134],
    [6, 34, 60, 86, 112, 138],
    [6, 30, 58, 86, 114, 142],
    [6, 34, 62, 90, 118, 146],
    [6, 30, 54, 78, 102, 126, 150],
    [6, 24, 50, 76, 102, 128, 154],
    [6, 28, 54, 80, 106, 132, 158],
    [6, 32, 58, 84, 110, 136, 162],
    [6, 26, 54, 82, 110, 138, 166],
    [6, 30, 58, 86, 114, 142, 170],
]

G15 = (1 << 10) | (1 << 8) | (1 << 5) | (1 << 4) | (1 << 2) | (1 << 1) | (1 << 0)
G18 = (
    (1 << 12)
    | (1 << 11)
    | (1 << 10)
    | (1 << 9)
    | (1 << 8)
    | (1 << 5)
    | (1 << 2)
    | (1 << 0)
)
G15_MASK = (1 << 14) | (1 << 12) | (1 << 10) | (1 << 4) | (1 << 1)

PAD0 = 0xEC
PAD1 = 0x11


# Precompute bit count limits, indexed by error correction level and code size.
def _data_count(block: base.RSBlock) -> int:
    """Return the data byte count for a single RS block (helper for BIT_LIMIT_TABLE).

    Args:
        block: An :class:`~qrcode.base.RSBlock` instance.

    Returns:
        The ``data_count`` attribute of *block*.
    """
    return block.data_count


BIT_LIMIT_TABLE: list[list[int]] = [
    [0]
    + [
        8 * sum(map(_data_count, base.rs_blocks(version, error_correction)))
        for version in range(1, 41)
    ]
    for error_correction in range(4)
]


def BCH_type_info(data: int) -> int:
    """Compute the BCH-encoded type information bits.

    The type information encodes the error correction level and mask pattern
    as a 15-bit string with BCH(15, 5) error correction.

    Args:
        data: 5-bit value combining error correction (high 2 bits) and
            mask pattern (low 3 bits).

    Returns:
        15-bit BCH-encoded integer for placement on the QR code grid.
    """
    d = data << 10
    while BCH_digit(d) - BCH_digit(G15) >= 0:
        d ^= G15 << (BCH_digit(d) - BCH_digit(G15))

    return ((data << 10) | d) ^ G15_MASK


def BCH_type_number(data: int) -> int:
    """Compute the BCH-encoded version number bits.

    Used for QR versions >= 7, which include a version information area
    encoded with BCH(18, 6).

    Args:
        data: Version number (7–40).

    Returns:
        18-bit BCH-encoded integer.
    """
    d = data << 12
    while BCH_digit(d) - BCH_digit(G18) >= 0:
        d ^= G18 << (BCH_digit(d) - BCH_digit(G18))
    return (data << 12) | d


def BCH_digit(data: int) -> int:
    """Return the bit-length of *data* (position of highest set bit + 1).

    Used internally by :func:`BCH_type_info` and :func:`BCH_type_number` to
    align polynomial terms during BCH encoding.

    Args:
        data: Non-negative integer whose bit-length is computed. ``0`` returns
            ``0``.

    Returns:
        Number of bits required to represent *data*.
    """
    digit = 0
    while data != 0:
        digit += 1
        data >>= 1
    return digit


def pattern_position(version: int) -> list[int]:
    """Return alignment pattern positions for the given version.

    Args:
        version: QR code version (1–40). Version 1 has no alignment patterns.

    Returns:
        List of row/column indices where alignment patterns should be placed.
    """
    return PATTERN_POSITION_TABLE[version - 1]


def mask_func(pattern: int) -> Callable[[int, int], bool]:
    """Return the mask function for the given mask pattern.

    The returned function takes *(row, col)* coordinates and returns ``True``
    when the module at that position should be inverted by the mask.

    Args:
        pattern: Mask pattern index 0–7 as defined in ISO/IEC 18004.

    Returns:
        A callable ``(row: int, col: int) -> bool``.

    Raises:
        TypeError: If *pattern* is not in range(8).
    """
    if pattern == 0:  # 000
        return lambda i, j: (i + j) % 2 == 0
    if pattern == 1:  # 001
        return lambda i, j: i % 2 == 0
    if pattern == 2:  # 010
        return lambda i, j: j % 3 == 0
    if pattern == 3:  # 011
        return lambda i, j: (i + j) % 3 == 0
    if pattern == 4:  # 100
        return lambda i, j: (math.floor(i / 2) + math.floor(j / 3)) % 2 == 0
    if pattern == 5:  # 101
        return lambda i, j: (i * j) % 2 + (i * j) % 3 == 0
    if pattern == 6:  # 110
        return lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0
    if pattern == 7:  # 111
        return lambda i, j: ((i * j) % 3 + (i + j) % 2) % 2 == 0
    raise TypeError("Bad mask pattern: " + str(pattern))  # pragma: no cover


def mode_sizes_for_version(version: int) -> dict[int, int]:
    """Return the character count indicator bit sizes for a given version.

    Args:
        version: QR code version (1–40).

    Returns:
        Mapping from encoding mode to the number of bits used for the
        character count indicator at that version.
    """
    if version < 10:
        return MODE_SIZE_SMALL
    if version < 27:
        return MODE_SIZE_MEDIUM
    return MODE_SIZE_LARGE


def length_in_bits(mode: int, version: int) -> int:
    """Return the character count indicator bit size for *mode* at *version*.

    Args:
        mode: One of :data:`MODE_NUMBER`, :data:`MODE_ALPHA_NUM`,
            :data:`MODE_8BIT_BYTE`, or :data:`MODE_KANJI`.
        version: QR code version (1–40).

    Returns:
        Number of bits for the character count indicator.

    Raises:
        TypeError: If *mode* is not a valid encoding mode.
        ValueError: If *version* is out of range.
    """
    if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE, MODE_KANJI):
        raise TypeError(f"Invalid mode ({mode})")  # pragma: no cover

    check_version(version)

    return mode_sizes_for_version(version)[mode]


def check_version(version: int) -> None:
    """Validate that *version* is in the valid range (1–40).

    Raises:
        ValueError: If *version* < 1 or > 40.
    """
    if version < 1 or version > 40:
        raise ValueError(f"Invalid version (was {version}, expected 1 to 40)")


def lost_point(modules: list[list[bool]]) -> int:
    """Compute the total penalty score for a QR code module matrix.

    The penalty evaluation follows ISO/IEC 18004 Annex J and is used to
    select the best mask pattern (lowest score wins).

    Args:
        modules: 2-D boolean array of the QR code grid.

    Returns:
        Total penalty score across all four evaluation levels.
    """
    modules_count = len(modules)

    lost_point = 0

    lost_point = _lost_point_level1(modules, modules_count)
    lost_point += _lost_point_level2(modules, modules_count)
    lost_point += _lost_point_level3(modules, modules_count)
    lost_point += _lost_point_level4(modules, modules_count)

    return lost_point


def _lost_point_level1(modules: list[list[bool]], modules_count: int) -> int:
    """Level 1 penalty: consecutive same-colour modules in row/column.

    Penalises runs of 5+ identical modules (finder-like patterns).
    """
    lost_point = 0

    modules_range = range(modules_count)
    container: list[int] = [0] * (modules_count + 1)

    for row in modules_range:
        this_row = modules[row]
        previous_color = this_row[0]
        length = 0
        for col in modules_range:
            if this_row[col] == previous_color:
                length += 1
            else:
                if length >= 5:
                    container[length] += 1
                length = 1
                previous_color = this_row[col]
        if length >= 5:
            container[length] += 1

    for col in modules_range:
        previous_color = modules[0][col]
        length = 0
        for row in modules_range:
            if modules[row][col] == previous_color:
                length += 1
            else:
                if length >= 5:
                    container[length] += 1
                length = 1
                previous_color = modules[row][col]
        if length >= 5:
            container[length] += 1

    lost_point += sum(
        container[each_length] * (each_length - 2)
        for each_length in range(5, modules_count + 1)
    )

    return lost_point


def _lost_point_level2(modules: list[list[bool]], modules_count: int) -> int:
    """Level 2 penalty: 2×2 blocks of same colour (module count × 3)."""
    lost_point = 0

    for row in range(modules_count - 1):
        for col in range(modules_count - 1):
            if (
                modules[row][col]
                == modules[row][col + 1]
                == modules[row + 1][col]
                == modules[row + 1][col + 1]
            ):
                lost_point += 3

    return lost_point


def _lost_point_level3(modules: list[list[bool]], modules_count: int) -> int:
    """Level 3 penalty: finder-like patterns (40 × 10 × 10 + white)."""
    lost_point = 0

    modules_range = range(modules_count)

    for row in modules_range:
        for col in range(modules_count - 10):
            pattern = modules[row][col : col + 11]
            if (
                pattern[0] is True
                and pattern[1] is False
                and pattern[2] is True
                and pattern[3] is True
                and pattern[4] is True
                and pattern[5] is False
                and pattern[6] is True
                and pattern[7] is False
                and pattern[8] is False
                and pattern[9] is False
                and pattern[10] is False
            ):
                lost_point += 40

    for col in modules_range:
        for row in range(modules_count - 10):
            pattern = [modules[r][col] for r in range(row, row + 11)]
            if (
                pattern[0] is True
                and pattern[1] is False
                and pattern[2] is True
                and pattern[3] is True
                and pattern[4] is True
                and pattern[5] is False
                and pattern[6] is True
                and pattern[7] is False
                and pattern[8] is False
                and pattern[9] is False
                and pattern[10] is False
            ):
                lost_point += 40

    return lost_point


def _lost_point_level4(modules: list[list[bool]], modules_count: int) -> int:
    """Level 4 penalty: dark/light ratio deviation (5% per 5% off 50%)."""
    dark_modules = 0

    for row in range(modules_count):
        for col in range(modules_count):
            if modules[row][col]:
                dark_modules += 1

    percent = dark_modules * 100 / (modules_count * modules_count)
    dev5 = ((percent - 50) + 24) // 5 * 5
    if dev5 < 0:
        dev5 -= 5

    return int(dev5)


def _split_by_pattern(pattern: bytes, data: bytes) -> Generator[tuple[bool, bytes]]:
    """Split *data* into alternating matched/unmatched segments.

    Args:
        pattern: Regex byte pattern to match against.
        data: Input byte string.

    Returns:
        List of ``(is_match, segment)`` tuples. Matched segments appear first
        in each pair.
    """
    result: list[tuple[bool, bytes]] = []  # noqa: F841
    while data:
        match = re.search(pattern, data)
        if not match:
            break
        start, end = match.start(), match.end()
        if start:
            yield False, data[:start]
        yield True, data[start:end]
        data = data[end:]
    if data:
        yield False, data


def to_bytestring(data: str | bytes) -> bytes:
    """Convert *data* to UTF-8 encoded bytes.

    If already bytes, returns the input unchanged. Strings are encoded as
    UTF-8.

    Args:
        data: Input string or byte string.

    Returns:
        UTF-8 encoded bytes.
    """
    if not isinstance(data, bytes):
        data = str(data).encode("utf-8")
    return data


def optimal_mode(data: bytes) -> int:
    """Determine the most compact encoding mode for *data*.

    Checks in order: numeric → alphanumeric → 8-bit byte.

    Args:
        data: Byte string to analyse (already UTF-8 encoded).

    Returns:
        One of :data:`MODE_NUMBER`, :data:`MODE_ALPHA_NUM`, or
        :data:`MODE_8BIT_BYTE`.
    """
    if data.isdigit():
        return MODE_NUMBER
    if RE_ALPHA_NUM.match(data):
        return MODE_ALPHA_NUM
    return MODE_8BIT_BYTE


class QRData:
    """Hold data in a QR-compatible encoding format.

    Supports numeric, alphanumeric, and 8-bit byte modes. KANJI mode is not
    currently implemented.

    Args:
        data: Content to encode (string or bytes). Will be UTF-8 encoded if
            a string.
        mode: Explicit encoding mode override. If ``None``, the most compact
            mode is chosen automatically via :func:`optimal_mode`.
        check_data: If ``True`` (default), validate that *data* is compatible
            with the requested *mode*.

    Attributes:
        mode: The selected encoding mode constant.
        data: The raw byte content to encode.

    Raises:
        TypeError: If *mode* is not a valid encoding mode.
        ValueError: If *data* cannot be represented in the given *mode*.
    """

    def __init__(
        self, data: str | bytes, mode: int | None = None, check_data: bool = True
    ) -> None:
        if check_data:
            data = to_bytestring(data)

        if mode is None:
            self.mode = optimal_mode(data)  # type: ignore[arg-type]
        else:
            self.mode = mode
            if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE):
                raise TypeError(f"Invalid mode ({mode})")  # pragma: no cover
            if check_data and mode < optimal_mode(data):  # type: ignore[arg-type] # pragma: no cover
                raise ValueError(f"Provided data can not be represented in mode {mode}")

        self.data = data

    def __len__(self) -> int:
        return len(self.data)

    def write(self, buffer: BitBuffer) -> None:
        """Encode this data chunk into the given :class:`BitBuffer`.

        The encoding follows ISO/IEC 18004 character encoding rules for the
        selected mode.

        Args:
            buffer: Target bit buffer to append encoded bits to.
        """
        if self.mode == MODE_NUMBER:
            for i in range(0, len(self.data), 3):
                chars = self.data[i : i + 3]
                bit_length = NUMBER_LENGTH[len(chars)]
                buffer.put(int(chars), bit_length)
        elif self.mode == MODE_ALPHA_NUM:
            for i in range(0, len(self.data), 2):
                chars = self.data[i : i + 2]
                if len(chars) > 1:
                    buffer.put(
                        ALPHA_NUM.find(chars[0]) * 45 + ALPHA_NUM.find(chars[1]),  # type: ignore[arg-type]
                        11,
                    )
                else:
                    buffer.put(ALPHA_NUM.find(chars), 6)  # type: ignore[arg-type]
        else:
            # Iterating a bytestring in Python 3 returns an integer,
            # no need to ord().
            data = self.data
            for c in data:
                buffer.put(c, 8)  # type: ignore[arg-type]

    def __repr__(self) -> str:
        return repr(self.data)


class BitBuffer:
    """Append-only bit-level buffer backed by a list of integers.

    Bits are packed MSB-first into each byte. Use :meth:`put` to append
    multi-bit values and :meth:`get` to read individual bits.
    """

    def __init__(self) -> None:
        self.buffer: list[int] = []
        self.length = 0

    def __repr__(self) -> str:
        return ".".join([str(n) for n in self.buffer])

    def get(self, index: int) -> bool:
        """Return the bit at position *index*.

        Args:
            index: Zero-based bit position.

        Returns:
            ``True`` if the bit is set, ``False`` otherwise.
        """
        buf_index = math.floor(index / 8)
        return ((self.buffer[buf_index] >> (7 - index % 8)) & 1) == 1

    def put(self, num: int, length: int) -> None:
        """Append *length* bits from the binary representation of *num*.

        Bits are written MSB-first.

        Args:
            num: Integer value to encode (must fit in *length* bits).
            length: Number of bits to write.
        """
        for i in range(length):
            self.put_bit(((num >> (length - i - 1)) & 1) == 1)

    def __len__(self) -> int:
        return self.length

    def put_bit(self, bit: bool) -> None:
        """Append a single bit.

        Args:
            bit: ``True`` for dark/1, ``False`` for light/0.
        """
        buf_index = self.length // 8
        if len(self.buffer) <= buf_index:
            self.buffer.append(0)
        if bit:
            self.buffer[buf_index] |= 0x80 >> (self.length % 8)
        self.length += 1


def create_bytes(buffer: BitBuffer, rs_blocks: list[base.RSBlock]) -> list[int]:
    """Split the bit buffer into data and error-correcting code bytes.

    Applies Reed-Solomon error correction using the provided block layout.

    Args:
        buffer: Filled :class:`BitBuffer` with encoded data bits.
        rs_blocks: List of :class:`~qrcode.base.RSBlock` describing the
            error correction block structure for this version and EC level.

    Returns:
        Interleaved list of data bytes followed by EC bytes, ready to be
        mapped onto the QR code grid.
    """
    offset = 0

    max_dc_count = 0
    max_ec_count = 0

    dcdata: list[list[int]] = []
    ecdata: list[list[int]] = []

    for rs_block in rs_blocks:
        dc_count = rs_block.data_count
        ec_count = rs_block.total_count - dc_count

        max_dc_count = max(max_dc_count, dc_count)
        max_ec_count = max(max_ec_count, ec_count)

        current_dc = [0xFF & buffer.buffer[i + offset] for i in range(dc_count)]
        offset += dc_count

        # Get error correction polynomial.
        if ec_count in LUT.rsPoly_LUT:
            rs_poly = base.Polynomial(LUT.rsPoly_LUT[ec_count], 0)
        else:
            rs_poly = base.Polynomial([1], 0)
            for i in range(ec_count):
                rs_poly = rs_poly * base.Polynomial([1, base.gexp(i)], 0)

        raw_poly = base.Polynomial(current_dc, len(rs_poly) - 1)

        mod_poly = raw_poly % rs_poly
        current_ec: list[int] = []
        mod_offset = len(mod_poly) - ec_count
        for i in range(ec_count):
            mod_index = i + mod_offset
            current_ec.append(mod_poly[mod_index] if (mod_index >= 0) else 0)

        dcdata.append(current_dc)
        ecdata.append(current_ec)

    data: list[int] = []
    for i in range(max_dc_count):
        for dc in dcdata:
            if i < len(dc):
                data.append(dc[i])
    for i in range(max_ec_count):
        for ec in ecdata:
            if i < len(ec):
                data.append(ec[i])

    return data


def create_data(
    version: int, error_correction: int, data_list: list[QRData]
) -> list[int]:
    """Create the final byte array for a QR code.

    Encodes all data chunks with their mode indicators and character counts,
    adds termination bits, applies padding, splits into RS blocks, and
    interleaves data + error correction bytes.

    Args:
        version: QR code version (1–40).
        error_correction: Error correction level constant.
        data_list: List of :class:`QRData` chunks to encode.

    Returns:
        Byte array ready for mapping onto the module grid.

    Raises:
        exceptions.DataOverflowError: If total encoded bits exceed the
            capacity for this version and error correction level.
    """
    buffer = BitBuffer()
    for data in data_list:
        buffer.put(data.mode, 4)
        buffer.put(len(data), length_in_bits(data.mode, version))
        data.write(buffer)

    # Calculate the maximum number of bits for the given version.
    rs_blocks = base.rs_blocks(version, error_correction)
    bit_limit = sum(block.data_count * 8 for block in rs_blocks)
    if len(buffer) > bit_limit:
        raise exceptions.DataOverflowError(
            f"Code length overflow. Data size ({len(buffer)}) > "
            f"size available ({bit_limit})"
        )

    # Terminate the bits (add up to four 0s).
    for _ in range(min(bit_limit - len(buffer), 4)):
        buffer.put_bit(False)

    # Delimit the string into 8-bit words, padding with 0s if necessary.
    delimit = len(buffer) % 8
    if delimit:
        for _ in range(8 - delimit):
            buffer.put_bit(False)

    # Add special alternating padding bitstrings until buffer is full.
    bytes_to_fill = (bit_limit - len(buffer)) // 8
    for i in range(bytes_to_fill):
        if i % 2 == 0:
            buffer.put(PAD0, 8)
        else:
            buffer.put(PAD1, 8)

    return create_bytes(buffer, rs_blocks)


def optimal_data_chunks(data: str | bytes, minimum: int = 20) -> list[QRData]:
    """Split *data* into optimally-encoded chunks.

    Scans the input for runs of at least *minimum* characters that can use a
    more compact encoding mode (numeric or alphanumeric vs byte). Mixed-type
    data benefits from this splitting because each chunk gets its own mode
    indicator, reducing overhead compared to using 8-bit byte mode for
    everything.

    Args:
        data: Input string or bytes.
        minimum: Minimum run length to trigger a separate optimised chunk.
            Set to ``0`` to disable splitting (single byte-mode chunk).

    Returns:
        List of :class:`QRData` instances, each with the best mode for its
        segment.
    """
    if not isinstance(data, bytes):
        data = data.encode("utf-8")

    # When data is shorter than minimum, use optimal mode for entire string
    if minimum and len(data) <= minimum:
        return [QRData(data, mode=optimal_mode(data), check_data=False)]

    chunks: list[QRData] = []
    num_pattern = re.compile(
        rb"\d" + (b"{" + str(minimum).encode() + b",}" if minimum else b"+")
    )
    alpha_num_bytes = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 $%*+-./:"
    alpha_pattern = re.compile(
        rb"["
        + re.escape(alpha_num_bytes)
        + rb"]"
        + (b"{" + str(minimum).encode() + b",}" if minimum else b"+")
    )

    for is_num, chunk in _optimal_split(data, num_pattern):
        if is_num:
            chunks.append(QRData(chunk, mode=MODE_NUMBER, check_data=False))
        else:
            for is_alpha, sub_chunk in _optimal_split(chunk, alpha_pattern):
                mode = MODE_ALPHA_NUM if is_alpha else MODE_8BIT_BYTE
                chunks.append(QRData(sub_chunk, mode=mode, check_data=False))

    return chunks


def _optimal_split(data: bytes, pattern: re.Pattern[bytes]) -> list[tuple[bool, bytes]]:
    """Split *data* into alternating matched/unmatched segments.

    Yields ``(is_match, segment)`` tuples for each portion of the input.
    Non-matching portions between matches are always yielded to ensure no
    data is lost.

    Args:
        data: Input byte string.
        pattern: Compiled regex pattern to search for.

    Returns:
        List of ``(is_match, segment)`` tuples covering all input bytes.
    """
    result: list[tuple[bool, bytes]] = []
    while data:
        match = re.search(pattern, data)
        if not match:
            break
        start, end = match.start(), match.end()
        if start:
            result.append((False, data[:start]))
        result.append((True, data[start:end]))
        data = data[end:]
    if data:
        result.append((False, data))
    return result
