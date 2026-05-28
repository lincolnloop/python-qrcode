"""Reed-Solomon error correction and Galois field arithmetic for QR codes.

This module implements the GF(256) arithmetic required by the Reed-Solomon
error-correction algorithm defined in ISO/IEC 18004. It provides:

- Lookup tables ``EXP_TABLE`` and ``LOG_TABLE`` for fast exponentiation /
  logarithm in the Galois field (``gexp()`` / ``glog()``).
- The :class:`Polynomial` class for polynomial arithmetic over GF(256).
- The :class:`~qrcode.base.RSBlock` named-tuple describing an error-correction block.
- The ``rs_blocks()`` function to look up the RS block layout for a given
  version and error correction level.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple, overload

from qrcode import constants

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__: list[str] = [
    "EXP_TABLE",
    "LOG_TABLE",
    "Polynomial",
    "RSBlock",
    "gexp",
    "glog",
    "rs_blocks",
]

# ---------------------------------------------------------------------------
# Galois field GF(256) lookup tables (generated at module load time)
# ---------------------------------------------------------------------------

EXP_TABLE: list[int] = list(range(256))

LOG_TABLE: list[int] = list(range(256))

for i in range(8):
    EXP_TABLE[i] = 1 << i

for i in range(8, 256):
    EXP_TABLE[i] = (
        EXP_TABLE[i - 4] ^ EXP_TABLE[i - 5] ^ EXP_TABLE[i - 6] ^ EXP_TABLE[i - 8]
    )

for i in range(255):
    LOG_TABLE[EXP_TABLE[i]] = i


# ---------------------------------------------------------------------------
# RS block table: indexed by (version-1)*4 + error_correction_offset
# Each row is a flat tuple of (count, total_count, data_count) triplets.
# Some entries have two groups with different sizes.
# ---------------------------------------------------------------------------

RS_BLOCK_OFFSET: dict[int, int] = {
    constants.ERROR_CORRECT_L: 0,
    constants.ERROR_CORRECT_M: 1,
    constants.ERROR_CORRECT_Q: 2,
    constants.ERROR_CORRECT_H: 3,
}

RS_BLOCK_TABLE: tuple[tuple[int, ...], ...] = (
    # L   M   Q   H   # version
    # 1
    (1, 26, 19),
    (1, 26, 16),
    (1, 26, 13),
    (1, 26, 9),
    # 2
    (1, 44, 34),
    (1, 44, 28),
    (1, 44, 22),
    (1, 44, 16),
    # 3
    (1, 70, 55),
    (1, 70, 44),
    (2, 35, 17),
    (2, 35, 13),
    # 4
    (1, 100, 80),
    (2, 50, 32),
    (2, 50, 24),
    (4, 25, 9),
    # 5
    (1, 134, 108),
    (2, 67, 43),
    (2, 33, 15, 2, 34, 16),
    (2, 33, 11, 2, 34, 12),
    # 6
    (2, 86, 68),
    (4, 43, 27),
    (4, 43, 19),
    (4, 43, 15),
    # 7
    (2, 98, 78),
    (4, 49, 31),
    (2, 32, 14, 4, 33, 15),
    (4, 39, 13, 1, 40, 14),
    # 8
    (2, 121, 97),
    (2, 60, 38, 2, 61, 39),
    (4, 40, 18, 2, 41, 19),
    (4, 40, 14, 2, 41, 15),
    # 9
    (2, 146, 116),
    (3, 58, 36, 2, 59, 37),
    (4, 36, 16, 4, 37, 17),
    (4, 36, 12, 4, 37, 13),
    # 10
    (2, 86, 68, 2, 87, 69),
    (4, 69, 43, 1, 70, 44),
    (6, 43, 19, 2, 44, 20),
    (6, 43, 15, 2, 44, 16),
    # 11
    (4, 101, 81),
    (1, 80, 50, 4, 81, 51),
    (4, 50, 22, 4, 51, 23),
    (3, 36, 12, 8, 37, 13),
    # 12
    (2, 116, 92, 2, 117, 93),
    (6, 58, 36, 2, 59, 37),
    (4, 46, 20, 6, 47, 21),
    (7, 42, 14, 4, 43, 15),
    # 13
    (4, 133, 107),
    (8, 59, 37, 1, 60, 38),
    (8, 44, 20, 4, 45, 21),
    (12, 33, 11, 4, 34, 12),
    # 14
    (3, 145, 115, 1, 146, 116),
    (4, 64, 40, 5, 65, 41),
    (11, 36, 16, 5, 37, 17),
    (11, 36, 12, 5, 37, 13),
    # 15
    (5, 109, 87, 1, 110, 88),
    (5, 65, 41, 5, 66, 42),
    (5, 54, 24, 7, 55, 25),
    (11, 36, 12, 7, 37, 13),
    # 16
    (5, 122, 98, 1, 123, 99),
    (7, 73, 45, 3, 74, 46),
    (15, 43, 19, 2, 44, 20),
    (3, 45, 15, 13, 46, 16),
    # 17
    (1, 135, 107, 5, 136, 108),
    (10, 74, 46, 1, 75, 47),
    (1, 50, 22, 15, 51, 23),
    (2, 42, 14, 17, 43, 15),
    # 18
    (5, 150, 120, 1, 151, 121),
    (9, 69, 43, 4, 70, 44),
    (17, 50, 22, 1, 51, 23),
    (2, 42, 14, 19, 43, 15),
    # 19
    (3, 141, 113, 4, 142, 114),
    (3, 70, 44, 11, 71, 45),
    (17, 47, 21, 4, 48, 22),
    (9, 39, 13, 16, 40, 14),
    # 20
    (3, 135, 107, 5, 136, 108),
    (3, 67, 41, 13, 68, 42),
    (15, 54, 24, 5, 55, 25),
    (15, 43, 15, 10, 44, 16),
    # 21
    (4, 144, 116, 4, 145, 117),
    (17, 68, 42),
    (17, 50, 22, 6, 51, 23),
    (19, 46, 16, 6, 47, 17),
    # 22
    (2, 139, 111, 7, 140, 112),
    (17, 74, 46),
    (7, 54, 24, 16, 55, 25),
    (34, 37, 13),
    # 23
    (4, 151, 121, 5, 152, 122),
    (4, 75, 47, 14, 76, 48),
    (11, 54, 24, 14, 55, 25),
    (16, 45, 15, 14, 46, 16),
    # 24
    (6, 147, 117, 4, 148, 118),
    (6, 73, 45, 14, 74, 46),
    (11, 54, 24, 16, 55, 25),
    (30, 46, 16, 2, 47, 17),
    # 25
    (8, 132, 106, 4, 133, 107),
    (8, 75, 47, 13, 76, 48),
    (7, 54, 24, 22, 55, 25),
    (22, 45, 15, 13, 46, 16),
    # 26
    (10, 142, 114, 2, 143, 115),
    (19, 74, 46, 4, 75, 47),
    (28, 50, 22, 6, 51, 23),
    (33, 46, 16, 4, 47, 17),
    # 27
    (8, 152, 122, 4, 153, 123),
    (22, 73, 45, 3, 74, 46),
    (8, 53, 23, 26, 54, 24),
    (12, 45, 15, 28, 46, 16),
    # 28
    (3, 147, 117, 10, 148, 118),
    (3, 73, 45, 23, 74, 46),
    (4, 54, 24, 31, 55, 25),
    (11, 45, 15, 31, 46, 16),
    # 29
    (7, 146, 116, 7, 147, 117),
    (21, 73, 45, 7, 74, 46),
    (1, 53, 23, 37, 54, 24),
    (19, 45, 15, 26, 46, 16),
    # 30
    (5, 145, 115, 10, 146, 116),
    (19, 75, 47, 10, 76, 48),
    (15, 54, 24, 25, 55, 25),
    (23, 45, 15, 25, 46, 16),
    # 31
    (13, 145, 115, 3, 146, 116),
    (2, 74, 46, 29, 75, 47),
    (42, 54, 24, 1, 55, 25),
    (23, 45, 15, 28, 46, 16),
    # 32
    (17, 145, 115),
    (10, 74, 46, 23, 75, 47),
    (10, 54, 24, 35, 55, 25),
    (19, 45, 15, 35, 46, 16),
    # 33
    (17, 145, 115, 1, 146, 116),
    (14, 74, 46, 21, 75, 47),
    (29, 54, 24, 19, 55, 25),
    (11, 45, 15, 46, 46, 16),
    # 34
    (13, 145, 115, 6, 146, 116),
    (14, 74, 46, 23, 75, 47),
    (44, 54, 24, 7, 55, 25),
    (59, 46, 16, 1, 47, 17),
    # 35
    (12, 151, 121, 7, 152, 122),
    (12, 75, 47, 26, 76, 48),
    (39, 54, 24, 14, 55, 25),
    (22, 45, 15, 41, 46, 16),
    # 36
    (6, 151, 121, 14, 152, 122),
    (6, 75, 47, 34, 76, 48),
    (46, 54, 24, 10, 55, 25),
    (2, 45, 15, 64, 46, 16),
    # 37
    (17, 152, 122, 4, 153, 123),
    (29, 74, 46, 14, 75, 47),
    (49, 54, 24, 10, 55, 25),
    (24, 45, 15, 46, 46, 16),
    # 38
    (4, 152, 122, 18, 153, 123),
    (13, 74, 46, 32, 75, 47),
    (48, 54, 24, 14, 55, 25),
    (42, 45, 15, 32, 46, 16),
    # 39
    (20, 147, 117, 4, 148, 118),
    (40, 75, 47, 7, 76, 48),
    (43, 54, 24, 22, 55, 25),
    (10, 45, 15, 67, 46, 16),
    # 40
    (19, 148, 118, 6, 149, 119),
    (18, 75, 47, 31, 76, 48),
    (34, 54, 24, 34, 55, 25),
    (20, 45, 15, 61, 46, 16),
)


# ---------------------------------------------------------------------------
# Galois field helper functions
# ---------------------------------------------------------------------------


def glog(n: int) -> int:
    """Return the discrete logarithm of *n* in GF(256).

    Uses a precomputed lookup table for O(1) performance.

    Args:
        n: Field element (1–255). ``glog(0)`` is undefined and raises.

    Returns:
        Integer exponent *e* such that ``gexp(e) == n``.

    Raises:
        ValueError: If *n* < 1.
    """
    if n < 1:  # pragma: no cover
        raise ValueError(f"glog({n})")
    return LOG_TABLE[n]


def gexp(n: int) -> int:
    """Return ``0x01`` raised to the power *n* in GF(256).

    Uses a precomputed lookup table. The result wraps modulo 255 so that
    exponents outside [0, 254] are still valid.

    Args:
        n: Exponent (any integer; wrapped mod 255 internally).

    Returns:
        Field element value in range [1, 255].
    """
    return EXP_TABLE[n % 255]


# ---------------------------------------------------------------------------
# Polynomial arithmetic over GF(256)
# ---------------------------------------------------------------------------


class Polynomial:
    """Polynomial with coefficients in the Galois field GF(256).

    Coefficients are stored least-significant first (index 0 = constant term).
    Arithmetic operators work in GF(256): addition is XOR, multiplication uses
    ``gexp`` / ``glog`` lookup tables.

    Attributes:
        num: List of coefficient values (with leading zeros stripped).
    """

    def __init__(self, data: list[int], shift: int) -> None:
        """Create a polynomial from raw coefficients.

        Leading zero coefficients are stripped and *shift* trailing zeros are
        appended to account for multiplication by ``x**shift``.

        Args:
            data: Coefficient values (least-significant first). Must be non-empty
                after stripping leading zeros.
            shift: Number of trailing zeros to append (equivalent to multiplying
                the polynomial by ``x**shift``).

        Raises:
            ValueError: If *data* is empty or contains only zeros.
        """
        if not data:  # pragma: no cover
            raise ValueError(f"{len(data)}/{shift}")

        offset = 0
        for offset in range(len(data)):
            if data[offset] != 0:
                break

        self.num: list[int] = data[offset:] + [0] * shift

    @overload
    def __getitem__(self, index: int) -> int: ...

    @overload
    def __getitem__(self, index: slice) -> list[int]: ...

    def __getitem__(self, index: int | slice) -> int | list[int]:
        """Return coefficient at *index* (or a slice of coefficients)."""
        return self.num[index]  # type: ignore[return-value]

    def __iter__(self) -> Iterator[int]:
        """Iterate over all coefficients."""
        return iter(self.num)

    def __len__(self) -> int:
        """Return the number of coefficients (degree + 1)."""
        return len(self.num)

    def __mul__(self, other: Polynomial) -> Polynomial:
        """Multiply two GF(256) polynomials.

        Args:
            other: The second polynomial.

        Returns:
            A new :class:`Polynomial` representing the product.
        """
        num = [0] * (len(self) + len(other) - 1)

        for i, item in enumerate(self):
            for j, other_item in enumerate(other):
                if item == 0 or other_item == 0:
                    continue
                num[i + j] ^= gexp(glog(int(item)) + glog(int(other_item)))

        return Polynomial(num, 0)

    def __mod__(self, other: Polynomial) -> Polynomial:
        """Polynomial remainder (division) in GF(256).

        Args:
            other: The divisor polynomial.

        Returns:
            A new :class:`Polynomial` representing ``self mod other``.
        """
        difference = len(self) - len(other)
        if difference < 0:
            return self

        if self[0] == 0:
            num = list(self[1:])  # type: ignore[arg-type]
            if difference:
                num.append(0)
            return Polynomial(num, 0) % other

        ratio = glog(int(self[0])) - glog(int(other[0]))

        num = [
            int(item) ^ gexp(glog(int(other_item)) + ratio)
            for item, other_item in zip(self, other, strict=False)
        ]
        if difference:
            num.extend(list(self[-difference:]))  # type: ignore[arg-type]

        return Polynomial(num, 0) % other

    def __repr__(self) -> str:
        """Return a human-readable representation of the polynomial."""
        return f"Polynomial({self.num!r})"


# ---------------------------------------------------------------------------
# RS block description
# ---------------------------------------------------------------------------


class RSBlock(NamedTuple):
    """Description of a single Reed-Solomon error-correction block.

    Attributes:
        total_count: Total number of bytes in the block (data + EC).
        data_count: Number of data bytes (the remainder are EC bytes).
    """

    total_count: int
    data_count: int

    def __repr__(self) -> str:
        """Return ``RSBlock(total=..., data=...)``."""
        return (
            f"RSBlock(total_count={self.total_count!r}, data_count={self.data_count!r})"
        )


# ---------------------------------------------------------------------------
# RS block lookup
# ---------------------------------------------------------------------------


def rs_blocks(version: int, error_correction: int) -> list[RSBlock]:
    """Return the Reed-Solomon block layout for a given version and EC level.

    Looks up the precomputed ``RS_BLOCK_TABLE`` and expands it into a flat
    list of :class:`RSBlock` instances (some versions use multiple blocks of
    different sizes).

    Args:
        version: QR code version (1–40).
        error_correction: One of
            :data:`~qrcode.constants.ERROR_CORRECT_L`, ``M``, ``Q``, or ``H``.

    Returns:
        List of :class:`RSBlock` describing each EC block.

    Raises:
        ValueError: If *error_correction* is not a recognized constant.
    """
    if error_correction not in RS_BLOCK_OFFSET:  # pragma: no cover
        raise ValueError(
            f"bad rs block @ version: {version} / error_correction: {error_correction}"
        )
    offset = RS_BLOCK_OFFSET[error_correction]
    rs_block = RS_BLOCK_TABLE[(version - 1) * 4 + offset]

    blocks: list[RSBlock] = []

    for i in range(0, len(rs_block), 3):
        count, total_count, data_count = rs_block[i : i + 3]
        for _ in range(count):
            blocks.append(RSBlock(total_count, data_count))

    return blocks
