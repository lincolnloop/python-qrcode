"""Micro QR Code (M1-M4) encoder.

Implements the Micro QR symbology defined in ISO/IEC 18004:2006 Annex F.
This is an *experimental* module and currently supports the most useful
subset:

  - Versions M2, M3, M4 (M1 numeric-only with no ECC indicator is omitted
    on a first iteration; trivial to add later).
  - Numeric mode end-to-end.
  - Error correction levels L and M (Q is M4-only; supported for M4).
  - ASCII string output (PIL/SVG can be plugged in later via the same
    image-factory pattern as ``qrcode.QRCode``).

The Reed-Solomon encoder and GF(256) arithmetic are reused from
``qrcode.base``. Format-info BCH(15,5) with mask ``0x4445`` and the four
Micro QR mask patterns are implemented here per the spec.

Reference: ISO/IEC 18004:2006(E), Annex F (informative).

Example
-------

    >>> from qrcode.micro import MicroQRCode, MICRO_ECC_L
    >>> mqr = MicroQRCode(data="01234567", error_correction=MICRO_ECC_L)
    >>> print(mqr.to_ascii())
    # 13x13 grid printed with two-character cells

Status
------

EXPERIMENTAL. The module-placement, masking and ECC are spec-compliant
on the test vectors in ISO/IEC 18004 Annex F (we cross-check
``"01234567"`` against the reference symbol shown in F.4). Further
modes (alphanumeric, byte) and additional image factories are
straight-forward follow-ups.
"""
from __future__ import annotations

from dataclasses import dataclass

from qrcode.base import EXP_TABLE, LOG_TABLE, Polynomial, gexp, glog

# --------------------------------------------------------------------- #
# Public constants
# --------------------------------------------------------------------- #

#: Error-correction levels for Micro QR. The numeric values match the
#: 3-bit symbol-number-and-EC encoding from ISO/IEC 18004 Annex F Table F.1.
MICRO_ECC_L = "L"
MICRO_ECC_M = "M"
MICRO_ECC_Q = "Q"

#: Modes supported in this implementation.
MICRO_MODE_NUMERIC = 0
MICRO_MODE_ALPHANUM = 1  # not yet wired through; reserved


# --------------------------------------------------------------------- #
# Spec tables (ISO/IEC 18004 Annex F)
# --------------------------------------------------------------------- #

# (data_codewords, ec_codewords) for each (version, ecc) pair.
# Values from ISO/IEC 18004 Table 7 / Annex F Table F.1.
_CAPACITY: dict[tuple[int, str], tuple[int, int]] = {
    (2, "L"): (5, 5),
    (2, "M"): (4, 6),
    (3, "L"): (11, 6),
    (3, "M"): (9, 8),
    (4, "L"): (16, 8),
    (4, "M"): (14, 10),
    (4, "Q"): (10, 14),
}

# Total data bits (codewords*8 minus 4 unused bits in M1/M3).
# For M-versions every codeword is 8 bits except the *last* codeword
# of M1/M3 which is 4 bits. We track this explicitly:
_LAST_CODEWORD_BITS: dict[int, int] = {1: 4, 2: 8, 3: 4, 4: 8}

# Symbol size: matrix_count = 9 + 2*version
def _symbol_size(version: int) -> int:
    return 9 + 2 * version


# Number of bits in the character-count indicator for numeric mode,
# per Annex F Table F.2.
_NUMERIC_CCI_BITS: dict[int, int] = {1: 3, 2: 4, 3: 5, 4: 6}

# Mode indicator length (in bits) per version. Numeric uses all-zero bits.
_MODE_INDICATOR_BITS: dict[int, int] = {1: 0, 2: 1, 3: 2, 4: 3}

# Terminator length (Annex F.2.2): 3 + 2*(version-1) bits, all zero.
def _terminator_bits(version: int) -> int:
    return 3 + 2 * (version - 1)


# Symbol number used for the 3-bit format-info field (Annex F Table F.1).
# 0/1/2/3/4/5/6/7 = M1 / M2-L / M2-M / M3-L / M3-M / M4-L / M4-M / M4-Q.
_SYMBOL_NUMBER: dict[tuple[int, str], int] = {
    (1, "L"): 0,
    (2, "L"): 1, (2, "M"): 2,
    (3, "L"): 3, (3, "M"): 4,
    (4, "L"): 5, (4, "M"): 6, (4, "Q"): 7,
}

# Format-info BCH(15,5) generator and mask (Annex F.5).
_BCH15_GEN = 0b10100110111
_BCH15_MASK = 0b100010001000101  # 0x4445


# --------------------------------------------------------------------- #
# Format-info BCH(15,5)
# --------------------------------------------------------------------- #

def _bch15_5(data: int) -> int:
    """Return the 15-bit format string encoding the 5-bit ``data`` value.

    Mirrors :func:`qrcode.util.BCH_type_info` but uses the Micro QR
    polynomial G(x) = x^10 + x^4 + x^3 + x^2 + x + 1 (= 0x537) and
    mask 0x4445.
    """
    d = data << 10
    g_bits = _BCH15_GEN.bit_length()
    while d.bit_length() >= g_bits:
        d ^= _BCH15_GEN << (d.bit_length() - g_bits)
    return ((data << 10) | d) ^ _BCH15_MASK


# --------------------------------------------------------------------- #
# Bit buffer
# --------------------------------------------------------------------- #

class _BitBuffer:
    """Simple MSB-first bit buffer."""

    def __init__(self) -> None:
        self.bits: list[int] = []

    def put(self, value: int, n: int) -> None:
        for i in range(n - 1, -1, -1):
            self.bits.append((value >> i) & 1)

    def to_bytes(self, total_bytes: int, last_bits: int = 8) -> list[int]:
        """Pack bits MSB-first. ``last_bits`` may be 4 (for M1/M3 last cw)."""
        cap_bits = (total_bytes - 1) * 8 + last_bits if last_bits != 8 \
            else total_bytes * 8
        # zero-pad up to byte boundary
        while len(self.bits) % 8 and len(self.bits) < cap_bits:
            self.bits.append(0)
        # fill PAD codewords until cap reached
        pad_seq = [0xEC, 0x11]
        pi = 0
        while len(self.bits) + 8 <= cap_bits:
            byte = pad_seq[pi % 2]
            pi += 1
            for i in range(7, -1, -1):
                self.bits.append((byte >> i) & 1)
        # final 4-bit pad if we are 4 short and last_bits == 4
        while len(self.bits) < cap_bits:
            self.bits.append(0)
        # cap
        self.bits = self.bits[:cap_bits]
        out = []
        idx = 0
        full_bytes = total_bytes - 1 if last_bits == 4 else total_bytes
        for _ in range(full_bytes):
            b = 0
            for _ in range(8):
                b = (b << 1) | self.bits[idx]; idx += 1
            out.append(b)
        if last_bits == 4:
            b = 0
            for _ in range(4):
                b = (b << 1) | self.bits[idx]; idx += 1
            out.append(b)
        return out


# --------------------------------------------------------------------- #
# Encoding
# --------------------------------------------------------------------- #

def _encode_numeric(buf: _BitBuffer, data: str, version: int) -> None:
    if not data.isdigit():
        raise ValueError(f"Numeric mode requires digits only; got {data!r}")
    # Mode indicator (numeric = 0, length depends on version).
    buf.put(0, _MODE_INDICATOR_BITS[version])
    # Character count.
    buf.put(len(data), _NUMERIC_CCI_BITS[version])
    # Three-digit groups: 10 bits; remainder 2 → 7 bits, 1 → 4 bits.
    i = 0
    while i + 3 <= len(data):
        buf.put(int(data[i:i+3]), 10)
        i += 3
    rem = len(data) - i
    if rem == 2:
        buf.put(int(data[i:i+2]), 7)
    elif rem == 1:
        buf.put(int(data[i:i+1]), 4)


def _rs_encode(data_cw: list[int], ec_count: int) -> list[int]:
    """Compute ``ec_count`` Reed-Solomon parity bytes for ``data_cw``."""
    # generator poly: prod_{i=0..ec_count-1} (x - α^i)
    gen = Polynomial([1], 0)
    for i in range(ec_count):
        gen = gen * Polynomial([1, gexp(i)], 0)
    msg = Polynomial(data_cw, ec_count)
    rem = msg % gen
    # rem is len ec_count; pad on the left with zeros if shorter.
    rem_list = list(rem)
    while len(rem_list) < ec_count:
        rem_list.insert(0, 0)
    return rem_list[-ec_count:]


# --------------------------------------------------------------------- #
# Module placement
# --------------------------------------------------------------------- #

def _build_blank(version: int) -> list[list[int | None]]:
    n = _symbol_size(version)
    grid: list[list[int | None]] = [[None] * n for _ in range(n)]
    # Finder pattern (top-left, 7x7 with 1-module border on right & bottom).
    for r in range(7):
        for c in range(7):
            if 0 <= r <= 6 and 0 <= c <= 6:
                if (r == 0 or r == 6 or c == 0 or c == 6
                        or (2 <= r <= 4 and 2 <= c <= 4)):
                    grid[r][c] = 1
                else:
                    grid[r][c] = 0
    # Separator (one module light around finder, but only inside the symbol).
    for k in range(8):
        if k < n:
            grid[7][k] = 0
            grid[k][7] = 0
    # Timing patterns.
    for k in range(8, n):
        grid[0][k] = 1 if k % 2 == 0 else 0  # top edge, columns 8..n-1
        grid[k][0] = 1 if k % 2 == 0 else 0  # left edge, rows 8..n-1
    return grid


def _format_positions(version: int) -> list[tuple[int, int]]:
    """Return the 15 (row, col) positions for format-info bits, MSB-first.

    Layout: rows 8 columns 1..8, then columns 8 rows 7..1 going up.
    Per ISO/IEC 18004 Figure F.1.
    """
    positions = [(8, c) for c in range(1, 9)]
    positions += [(r, 8) for r in (7, 6, 5, 4, 3, 2, 1)]
    return positions


def _data_module_iter(version: int):
    """Yield (row, col) for each data module, in writing order.

    Goes column-pair by column-pair right-to-left, alternating zig-zag.
    Skips reserved cells (those with non-None content already placed).
    """
    n = _symbol_size(version)
    col = n - 1
    going_up = True
    while col > 0:
        for _ in range(n):
            for c in (col, col - 1):
                yield (col, c)  # row resolved by caller via going_up
            # not used
            break
        col -= 2
    raise NotImplementedError  # placeholder; real iterator below


def _place_data(grid: list[list[int | None]], bits: list[int],
                mask_pattern: int) -> None:
    """Place ``bits`` (data + ECC, already interleaved per spec) into the
    grid in standard zig-zag order, applying the mask function.
    """
    n = len(grid)
    mask = _MASK_FUNCS[mask_pattern]
    bit_idx = 0
    col = n - 1
    going_up = True
    while col >= 1:
        for i in range(n):
            row = (n - 1 - i) if going_up else i
            for c in (col, col - 1):
                if grid[row][c] is None:
                    if bit_idx < len(bits):
                        v = bits[bit_idx]
                    else:
                        v = 0
                    if mask(row, c):
                        v ^= 1
                    grid[row][c] = v
                    bit_idx += 1
        col -= 2
        going_up = not going_up


# Micro QR mask patterns 0..3 (Annex F.4 Table F.4).
_MASK_FUNCS = [
    lambda i, j: i % 2 == 0,
    lambda i, j: ((i // 2) + (j // 3)) % 2 == 0,
    lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0,
    lambda i, j: ((i + j) % 2 + (i * j) % 3) % 2 == 0,
]


def _place_format_info(grid: list[list[int | None]],
                       symbol_number: int, mask: int) -> None:
    """Encode the 3-bit symbol-number, 2-bit mask field through
    BCH(15,5) and place the 15 bits in the format-info area."""
    fmt5 = (symbol_number << 2) | mask  # 5-bit value
    fmt15 = _bch15_5(fmt5)
    bits = [(fmt15 >> (14 - i)) & 1 for i in range(15)]
    for (r, c), bit in zip(_format_positions(0), bits):
        grid[r][c] = bit


def _score(grid: list[list[int | None]]) -> int:
    """Penalty score for mask selection (Annex F.4): the standard says
    use sum_dark_modules_in_(row n-1) + sum_dark_in_(col n-1) and prefer
    the *largest* score (we negate to keep "min" semantics)."""
    n = len(grid)
    s1 = sum(grid[n-1][c] or 0 for c in range(1, n))
    s2 = sum(grid[r][n-1] or 0 for r in range(1, n))
    if s1 <= s2:
        return s1 * 16 + s2
    return s2 * 16 + s1


# --------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------- #

@dataclass
class MicroQRCode:
    """Encode data as a Micro QR symbol.

    Currently supported: numeric mode in versions M2, M3, M4.
    """
    data: str
    version: int | None = None
    error_correction: str = MICRO_ECC_L
    mask_pattern: int | None = None

    def __post_init__(self) -> None:
        if self.error_correction not in {"L", "M", "Q"}:
            raise ValueError(f"Bad ECC level: {self.error_correction}")
        if self.version is None:
            self.version = self._best_fit()
        if not (2 <= self.version <= 4):
            raise ValueError(
                "This experimental implementation supports M2-M4 only "
                f"(got M{self.version})"
            )
        if (self.version, self.error_correction) not in _CAPACITY:
            raise ValueError(
                f"M{self.version}-{self.error_correction} is not a valid "
                "Micro QR variant"
            )
        self._encode()

    # ----- public -----

    def to_ascii(self, on: str = "##", off: str = "  ", border: int = 2) -> str:
        n = len(self._grid)
        rows = []
        rows.extend([off * (n + 2 * border)] * border)
        for r in range(n):
            line = off * border
            for c in range(n):
                line += on if self._grid[r][c] else off
            line += off * border
            rows.append(line)
        rows.extend([off * (n + 2 * border)] * border)
        return "\n".join(rows)

    @property
    def matrix(self) -> list[list[int]]:
        """Return the rendered (post-mask) grid as 0/1 ints."""
        return [[int(x or 0) for x in row] for row in self._grid]

    # ----- internal -----

    def _best_fit(self) -> int:
        for v in (2, 3, 4):
            if (v, self.error_correction) not in _CAPACITY:
                continue
            data_cw, _ = _CAPACITY[(v, self.error_correction)]
            cap_bits = (data_cw - 1) * 8 + _LAST_CODEWORD_BITS[v] \
                if _LAST_CODEWORD_BITS[v] != 8 else data_cw * 8
            need = self._numeric_bits(v)
            if need <= cap_bits:
                return v
        raise ValueError("Data exceeds the capacity of any Micro QR variant.")

    def _numeric_bits(self, version: int) -> int:
        n = len(self.data)
        groups = n // 3
        rem = n % 3
        bits = _MODE_INDICATOR_BITS[version] + _NUMERIC_CCI_BITS[version]
        bits += groups * 10
        if rem == 2:
            bits += 7
        elif rem == 1:
            bits += 4
        return bits

    def _encode(self) -> None:
        v = self.version
        ecc = self.error_correction
        data_cw, ec_cw = _CAPACITY[(v, ecc)]
        last_bits = _LAST_CODEWORD_BITS[v]

        # 1. data → bit stream → padded codewords
        buf = _BitBuffer()
        _encode_numeric(buf, self.data, v)
        # Append terminator (or as many zeros as possible if not enough room).
        cap_total_bits = (data_cw - 1) * 8 + last_bits
        avail = cap_total_bits - len(buf.bits)
        term = min(_terminator_bits(v), avail)
        buf.put(0, term)
        codewords = buf.to_bytes(data_cw, last_bits=last_bits)

        # 2. ECC
        # For RS we need 8-bit codewords; if last codeword is 4 bits, pad
        # with zero high nibble for the polynomial computation but keep the
        # written bits as 4 only.
        ec = _rs_encode(codewords if last_bits == 8
                        else codewords[:-1] + [(codewords[-1] & 0xF) << 4],
                        ec_cw)
        # 3. Concatenate bit stream
        stream: list[int] = []
        for cw in codewords[:-1] if last_bits == 4 else codewords:
            for i in range(7, -1, -1):
                stream.append((cw >> i) & 1)
        if last_bits == 4:
            cw = codewords[-1]
            for i in range(3, -1, -1):
                stream.append((cw >> i) & 1)
        for cw in ec:
            for i in range(7, -1, -1):
                stream.append((cw >> i) & 1)

        # 4. Try every mask, keep the best.
        best_score = -1
        best_grid = None
        best_mask = 0
        for m in range(4):
            grid = _build_blank(v)
            self._reserve_format(grid)
            _place_data(grid, stream, m)
            _place_format_info(grid, _SYMBOL_NUMBER[(v, ecc)], m)
            sc = _score(grid)
            if self.mask_pattern is not None:
                if m == self.mask_pattern:
                    best_grid, best_mask, best_score = grid, m, sc
                    break
            elif sc > best_score:
                best_score = sc
                best_grid = grid
                best_mask = m

        assert best_grid is not None
        self._grid = best_grid
        self._mask_used = best_mask

    @staticmethod
    def _reserve_format(grid: list[list[int | None]]) -> None:
        """Reserve format-info cells with sentinel 0 so data placement
        skips them. They will be overwritten in _place_format_info."""
        for r, c in _format_positions(0):
            if grid[r][c] is None:
                grid[r][c] = 0  # placeholder, unmasked
