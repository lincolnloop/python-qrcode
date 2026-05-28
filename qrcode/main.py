from __future__ import annotations

import sys
from bisect import bisect_left
from typing import Any, Generic, NamedTuple, TextIO, TypeVar, cast

from qrcode import base, constants, exceptions, util
from qrcode.image.base import BaseImage
from qrcode.image.pure import PyPNGImage

ModulesType = list[list[bool | None]]
# Cache modules generated just based on the QR Code version
precomputed_qr_blanks: dict[int, ModulesType] = {}

__all__: list[str] = [
    "ActiveWithNeighbors",
    "QRCode",
    "make",
]


def make(
    data: str | bytes | util.QRData | None = None,
    **kwargs: Any,
) -> BaseImage:
    """Generate a QR code image for the given data.

    This is the simplest convenience function — it creates a :class:`QRCode`
    instance with default settings, adds the provided data, and returns an
    image object ready to be saved or displayed.

    Args:
        data: The content to encode. Can be a string, bytes, or a
            :class:`~qrcode.util.QRData` instance. Set to ``None`` if you
            plan to call :meth:`QRCode.add_data` manually before calling
            :meth:`QRCode.make_image`.
        **kwargs: Additional keyword arguments forwarded to the
            :class:`QRCode` constructor and/or the image factory. Common
            options include:

            - ``version`` (int | None): QR code version 1–40, or ``None``
              for automatic sizing.
            - ``error_correction`` (int): One of
              :data:`~qrcode.ERROR_CORRECT_L`, ``_M``, ``_Q``, ``_H``.
            - ``box_size`` (int): Pixel size per module (default 10).
            - ``border`` (int): Quiet zone in modules (default 4, min 4
              per spec).
            - ``image_factory``: A :class:`~qrcode.image.base.BaseImage`
              subclass for custom rendering.
            - ``mask_pattern`` (int | None): Mask pattern 0–7, or ``None``
              to auto-select the best one.

    Returns:
        An image object (typically a PIL Image wrapper or PyPNGImage) that
        supports :meth:`~qrcode.image.base.BaseImage.save` and optionally
        :meth:`~PIL.Image.Image.show`.

    Example:
        >>> import qrcode
        >>> img = qrcode.make("https://example.com")
        >>> img.save("qr.png")
    """
    qr = QRCode(**kwargs)
    if data is not None:
        qr.add_data(data)
    return qr.make_image()


def _check_box_size(size: int) -> None:
    """Validate that *size* is a positive integer."""
    if int(size) <= 0:
        raise ValueError(f"Invalid box size (was {size}, expected larger than 0)")


def _check_border(size: int) -> None:
    """Validate that *size* is zero or positive."""
    if int(size) < 0:
        raise ValueError(
            f"Invalid border value (was {size}, expected 0 or larger than that)"
        )


def _check_mask_pattern(mask_pattern: int | None) -> None:
    """Validate *mask_pattern* is ``None`` or an integer in range(8)."""
    if mask_pattern is None:
        return
    if not isinstance(mask_pattern, int):
        raise TypeError(
            f"Invalid mask pattern (was {type(mask_pattern)}, expected int)"
        )
    if mask_pattern < 0 or mask_pattern > 7:
        raise ValueError(f"Mask pattern should be in range(8) (got {mask_pattern})")


def copy_2d_array(x: ModulesType) -> ModulesType:
    """Return a deep copy of a 2-D boolean array."""
    return [row[:] for row in x]


class ActiveWithNeighbors(NamedTuple):
    """9-cell neighbourhood around a module (3×3 grid).

    Attributes:
        NW: Top-left neighbour is dark.
        N: Top neighbour is dark.
        NE: Top-right neighbour is dark.
        W: Left neighbour is dark.
        me: Centre cell is dark.
        E: Right neighbour is dark.
        SW: Bottom-left neighbour is dark.
        S: Bottom neighbour is dark.
        SE: Bottom-right neighbour is dark.
    """

    NW: bool
    N: bool
    NE: bool
    W: bool
    me: bool
    E: bool
    SW: bool
    S: bool
    SE: bool

    def __bool__(self) -> bool:
        return self.me


GenericImage = TypeVar("GenericImage", bound=BaseImage)
GenericImageLocal = TypeVar("GenericImageLocal", bound=BaseImage)


class QRCode(Generic[GenericImage]):
    """Main class for building QR codes with full control.

    Create an instance, add data via :meth:`add_data`, then call
    :meth:`make_image` to get a renderable image object.

    Args:
        version: QR code version (1–40). ``None`` means auto-size to fit
            the data. Higher versions produce larger codes that hold more
            data.
        error_correction: One of :data:`ERROR_CORRECT_L` (7%),
            :data:`ERROR_CORRECT_M` (15%, default),
            :data:`ERROR_CORRECT_Q` (25%), or
            :data:`ERROR_CORRECT_H` (30%). Higher levels allow more damage
            tolerance but reduce capacity.
        box_size: Number of pixels per module (default 10). Larger values
            produce bigger images.
        border: Quiet zone width in modules (default 4). The QR spec
            requires a minimum of 4; use ``border=0`` for minimal output.
        image_factory: A :class:`~qrcode.image.base.BaseImage` subclass to
            control the rendering format. ``None`` selects PIL if available,
            otherwise PyPNG.
        mask_pattern: Mask pattern index (0–7) or ``None`` to auto-select
            the pattern with the lowest penalty score.

    Example:
        >>> import qrcode
        >>> qr = qrcode.QRCode(
        ...     version=1,
        ...     error_correction=qrcode.ERROR_CORRECT_H,
        ...     box_size=10,
        ... )
        >>> qr.add_data("Hello World")
        >>> img = qr.make_image()
        >>> img.save("qr.png")
    """

    modules: ModulesType
    _version: int | None = None

    def __init__(
        self,
        version: int | None = None,
        error_correction: int = constants.ERROR_CORRECT_M,
        box_size: int = 10,
        border: int = 4,
        image_factory: type[GenericImage] | None = None,
        mask_pattern: int | None = None,
    ) -> None:
        _check_box_size(box_size)
        _check_border(border)
        self.clear()
        self.version = version
        self.error_correction = int(error_correction)
        self.box_size = int(box_size)
        # Spec says border should be at least four boxes wide, but allow for
        # any (e.g. for producing printable QR codes).
        self.border = int(border)
        self.mask_pattern = mask_pattern
        self.image_factory: type[BaseImage] | None = image_factory
        if image_factory is not None:
            assert issubclass(image_factory, BaseImage)

    @property
    def version(self) -> int:
        """Current QR code version (1–40). Auto-computed if not set."""
        if self._version is None:
            self.best_fit()
        return cast("int", self._version)

    @version.setter
    def version(self, value: int | None) -> None:
        if value is not None:
            value = int(value)
            util.check_version(value)
        self._version = value

    @property
    def mask_pattern(self) -> int | None:  # type: ignore[override]
        """Mask pattern (0–7) or ``None`` for auto-selection."""
        return self._mask_pattern

    @mask_pattern.setter
    def mask_pattern(self, pattern: int | None) -> None:
        _check_mask_pattern(pattern)
        self._mask_pattern = pattern

    def clear(self) -> None:
        """Reset all internal data and state.

        Call this to reuse the same ``QRCode`` instance for a different
        payload without creating a new object.
        """
        self.modules = [[]]
        self.modules_count = 0
        self.data_cache: list[int] | None = None
        self.data_list: list[util.QRData] = []
        self._version = None

    def add_data(self, data: str | bytes | util.QRData, optimize: int = 20) -> None:
        """Add data to this QR Code.

        Data can be added in multiple calls; all chunks are concatenated
        before encoding.

        Args:
            data: Content to encode (string, bytes, or :class:`~qrcode.util.QRData`).
            optimize: Data will be split into multiple chunks to optimise
                the QR size by finding more compressed modes of at least
                this length. Set to ``0`` to disable chunk optimisation.

        Raises:
            TypeError: If *data* is not a recognised type.
        """
        if isinstance(data, util.QRData):
            self.data_list.append(data)
        elif optimize:
            self.data_list.extend(util.optimal_data_chunks(data, minimum=optimize))
        else:
            self.data_list.append(util.QRData(data))
        self.data_cache = None

    def make(self, fit: bool = True) -> None:
        """Compile the data into a QR Code module matrix.

        Args:
            fit: If ``True`` (or if no version has been provided), find the
                smallest version that fits all added data. Set to ``False``
                to force use of the current version even if it overflows.

        Raises:
            exceptions.DataOverflowError: If the data does not fit in the
                selected version and *fit* is ``False``.
        """
        if fit or (self._version is None):
            self.best_fit(start=self._version)
        if self.mask_pattern is None:
            self.makeImpl(self.best_mask_pattern())
        else:
            self.makeImpl(self.mask_pattern)

    def makeImpl(self, mask_pattern: int) -> None:
        """Internal: build the full module matrix for the current version.

        This method places position detection patterns, timing patterns,
        alignment patterns, type information, and finally maps the encoded
        data bytes onto the grid using the chosen mask pattern.

        Args:
            mask_pattern: Integer 0–7 selecting the mask function.
        """
        self.modules_count = self.version * 4 + 17

        if self.version in precomputed_qr_blanks:
            self.modules = copy_2d_array(precomputed_qr_blanks[self.version])
        else:
            self.modules = [
                [None] * self.modules_count for _ in range(self.modules_count)
            ]
            self.setup_position_probe_pattern(0, 0)
            self.setup_position_probe_pattern(self.modules_count - 7, 0)
            self.setup_position_probe_pattern(0, self.modules_count - 7)
            self.setup_position_adjust_pattern()
            self.setup_timing_pattern()

            precomputed_qr_blanks[self.version] = copy_2d_array(self.modules)

        self.setup_type_info(mask_pattern)

        if self.version >= 7:
            self.setup_type_number()

        if self.data_cache is None:
            self.data_cache = util.create_data(
                self.version, self.error_correction, self.data_list
            )
        self.map_data(self.data_cache, mask_pattern)

    def setup_position_probe_pattern(self, row: int, col: int) -> None:
        """Place a 7×7 position detection pattern (finder + separator)."""
        for r in range(-1, 8):
            if row + r <= -1 or self.modules_count <= row + r:
                continue

            for c in range(-1, 8):
                if col + c <= -1 or self.modules_count <= col + c:
                    continue

                if (
                    (0 <= r <= 6 and c in {0, 6})
                    or (0 <= c <= 6 and r in {0, 6})
                    or (2 <= r <= 4 and 2 <= c <= 4)
                ):
                    self.modules[row + r][col + c] = True
                else:
                    self.modules[row + r][col + c] = False

    def check_data(self) -> None:
        """Validate that all added data fits within the current version."""
        if self.data_cache is not None:
            return

        rs_blocks = base.rs_blocks(self._version, self.error_correction)  # type: ignore[arg-type]
        bit_limit = sum(block.data_count * 8 for block in rs_blocks)

        buffer = util.BitBuffer()
        for data in self.data_list:
            buffer.put(data.mode, 4)
            buffer.put(len(data), util.length_in_bits(data.mode, self.version))
            data.write(buffer)

        if len(buffer) > bit_limit:
            raise exceptions.DataOverflowError(
                f"Code length overflow. Data size ({len(buffer)}) > "
                f"size available ({bit_limit})"
            )

    def print_tty(self, out: TextIO | None = None) -> None:
        """Output the QR Code only using TTY colors.

        If the data has not been compiled yet, make it first.

        Args:
            out: File-like object to write to. Defaults to ``sys.stdout``.

        Raises:
            OSError: If *out* is not a TTY (``isatty()`` returns ``False``).
        """
        if out is None:
            out = sys.stdout

        if not out.isatty():
            raise OSError("Not a tty")

        if self.data_cache is None:
            self.make()

        modcount = self.modules_count
        out.write("\x1b[1;47m" + (" " * (modcount * 2 + 4)) + "\x1b[0m\n")
        for r in range(modcount):
            out.write("\x1b[1;47m  \x1b[40m")
            for c in range(modcount):
                if self.modules[r][c]:
                    out.write("  ")
                else:
                    out.write("\x1b[1;47m  \x1b[40m")
            out.write("\x1b[1;47m  \x1b[0m\n")
        out.write("\x1b[1;47m" + (" " * (modcount * 2 + 4)) + "\x1b[0m\n")
        out.flush()

    def print_ascii(
        self,
        out: TextIO | None = None,
        tty: bool = False,
        invert: bool = False,
    ) -> None:
        """Output the QR Code using ASCII characters.

        Args:
            out: File-like object to write to. Defaults to ``sys.stdout``.
            tty: Use fixed TTY color codes (forces invert=True).
            invert: Invert the ASCII characters (solid <-> transparent).

        Raises:
            OSError: If *tty* is ``True`` and *out* is not a TTY.
        """
        if out is None:
            out = sys.stdout

        if tty and not out.isatty():
            raise OSError("Not a tty")

        if self.data_cache is None:
            self.make()

        modcount = self.modules_count
        codes = [bytes((code,)).decode("cp437") for code in (255, 223, 220, 219)]
        if tty:
            invert = True
        if invert:
            codes.reverse()

        def get_module(x: int, y: int) -> int:
            if invert and self.border and max(x, y) >= modcount + self.border:
                return 1
            if min(x, y) < 0 or max(x, y) >= modcount:
                return 0
            return cast("int", self.modules[x][y])

        for r in range(-self.border, modcount + self.border, 2):
            if tty:
                if not invert or r < modcount + self.border - 1:
                    out.write("\x1b[48;5;232m")  # Background black
                out.write("\x1b[38;5;255m")  # Foreground white
            for c in range(-self.border, modcount + self.border):
                pos = get_module(r, c) + (get_module(r + 1, c) << 1)
                out.write(codes[pos])
            if tty:
                out.write("\x1b[0m")
            out.write("\n")
        out.flush()

    def best_fit(self, start: int | None = None) -> int:
        """Find the smallest QR code version that fits all added data.

        Uses binary search on the bit-limit table for efficiency, then
        validates the selected version by attempting to encode the data.

        Args:
            start: Minimum version to try (default: 1).

        Returns:
            The selected QR code version.

        Raises:
            exceptions.DataOverflowError: If even version 40 cannot hold
                all added data.
        """
        if start is None:
            start = 1
        util.check_version(start)

        # Corresponds to the code in util.create_data, except we don't yet know
        # version, so optimistically assume start and check later
        mode_sizes = util.mode_sizes_for_version(start)
        buffer = util.BitBuffer()
        for data in self.data_list:
            buffer.put(data.mode, 4)
            buffer.put(len(data), mode_sizes[data.mode])
            data.write(buffer)

        needed_bits = len(buffer)
        # Create a thread-local copy of the table to avoid concurrent access issues (Python 3.13+)
        self._version = bisect_left(
            util.BIT_LIMIT_TABLE[self.error_correction][:], needed_bits, start
        )
        if self._version == 41:
            raise exceptions.DataOverflowError

        # Now check whether we need more bits for the mode sizes, recursing if
        # our guess was too low
        if mode_sizes is not util.mode_sizes_for_version(self._version):
            return self.best_fit(start=self._version)
        return cast("int", self._version)

    def _bit_size(self) -> int:
        """Return the total bit size of all data chunks."""
        buffer = util.BitBuffer()
        for data in self.data_list:
            buffer.put(data.mode, 4)
            # Use version 1 as fallback when _version is None (first entry in table)
            ver = self._version or 1
            buffer.put(len(data), util.length_in_bits(data.mode, ver))
            data.write(buffer)
        return len(buffer)

    def best_mask_pattern(self) -> int:
        """Select the mask pattern with the lowest penalty score.

        Returns:
            Integer 0–7 for the optimal mask pattern.
        """
        des = sys.maxsize
        count = 0
        for mask in range(8):
            self.makeImpl(mask)
            n = util.lost_point(cast("list[list[bool]]", self.modules))
            if des > n:
                des = n
                count = mask
        return count

    def make_image(
        self,
        image_factory: type[BaseImage] | None = None,
        **kwargs: object,
    ) -> BaseImage:
        """Render the QR code as an image.

        Args:
            image_factory: A :class:`~qrcode.image.base.BaseImage` subclass.
                If ``None``, uses the factory set during construction or falls
                back to PIL (if available) / PyPNG.
            **kwargs: Additional keyword arguments forwarded to the image
                factory constructor. For :class:`~qrcode.image.styledpil.StyledPilImage`
                these include ``module_drawer``, ``color_mask``, and
                ``embedded_image``.

        Returns:
            An image object ready for :meth:`~qrcode.image.base.BaseImage.save`.

        Raises:
            ValueError: If an embedded image is requested but error correction
                is not set to ``ERROR_CORRECT_H``.
        """
        if (
            kwargs.get("embedded_image") or kwargs.get("embedded_image_path")
        ) and self.error_correction != constants.ERROR_CORRECT_H:
            raise ValueError(
                "Error correction level must be ERROR_CORRECT_H if an embedded image is provided"
            )

        _check_box_size(self.box_size)
        if self.data_cache is None:
            self.make()

        if image_factory is not None:
            assert issubclass(image_factory, BaseImage)
        else:
            image_factory = self.image_factory
            if image_factory is None:
                from qrcode.image.pil import Image, PilImage  # noqa: PLC0415

                # Use PIL by default if available, otherwise use PyPNG.
                image_factory = PilImage if Image else PyPNGImage

        im = image_factory(
            self.border,
            self.modules_count,
            self.box_size,
            qrcode_modules=self.modules,
            **kwargs,
        )

        if im.needs_drawrect:
            for r in range(self.modules_count):
                for c in range(self.modules_count):
                    if im.needs_context:
                        im.drawrect_context(r, c, qr=self)
                    elif self.modules[r][c]:
                        im.drawrect(r, c)
        if im.needs_processing:
            im.process()

        return im

    # -- internal helpers --------------------------------------------------

    def is_constrained(self, row: int, col: int) -> bool:
        """Return ``True`` if *(row, col)* is inside the module grid."""
        return (
            row >= 0
            and row < len(self.modules)
            and col >= 0
            and col < len(self.modules[row])
        )

    def setup_timing_pattern(self) -> None:
        """Place horizontal and vertical timing patterns between finders."""
        for r in range(8, self.modules_count - 8):
            if self.modules[r][6] is not None:
                continue
            self.modules[r][6] = r % 2 == 0

        for c in range(8, self.modules_count - 8):
            if self.modules[6][c] is not None:
                continue
            self.modules[6][c] = c % 2 == 0

    def setup_position_adjust_pattern(self) -> None:
        """Place alignment patterns (version >= 2)."""
        pos = util.pattern_position(self.version)

        for i in range(len(pos)):
            row = pos[i]

            for j in range(len(pos)):
                col = pos[j]

                if self.modules[row][col] is not None:
                    continue

                for r in range(-2, 3):
                    for c in range(-2, 3):
                        if r in (-2, 2) or c in (-2, 2) or (r == 0 and c == 0):
                            self.modules[row + r][col + c] = True
                        else:
                            self.modules[row + r][col + c] = False

    def setup_type_number(self) -> None:
        """Place the version information (version >= 7)."""
        bits = util.BCH_type_number(self.version)

        for i in range(18):
            mod = ((bits >> i) & 1) == 1
            self.modules[i // 3][i % 3 + self.modules_count - 8 - 3] = mod

        for i in range(18):
            mod = ((bits >> i) & 1) == 1
            self.modules[i % 3 + self.modules_count - 8 - 3][i // 3] = mod

    def setup_type_info(self, mask_pattern: int) -> None:
        """Place the type information (error correction level + mask)."""
        data = (self.error_correction << 3) | mask_pattern
        bits = util.BCH_type_info(data)

        # vertical
        for i in range(15):
            mod = ((bits >> i) & 1) == 1

            if i < 6:
                self.modules[i][8] = mod
            elif i < 8:
                self.modules[i + 1][8] = mod
            else:
                self.modules[self.modules_count - 15 + i][8] = mod

        # horizontal
        for i in range(15):
            mod = ((bits >> i) & 1) == 1

            if i < 8:
                self.modules[8][self.modules_count - i - 1] = mod
            elif i < 9:
                self.modules[8][15 - i - 1 + 1] = mod
            else:
                self.modules[8][15 - i - 1] = mod

        # fixed module
        self.modules[self.modules_count - 8][8] = True

    def map_data(self, data: list[int], mask_pattern: int) -> None:
        """Map encoded data bytes onto the module grid with masking applied.

        Args:
            data: Byte array produced by :func:`~qrcode.util.create_data`.
            mask_pattern: Mask pattern index 0–7.
        """
        inc = -1
        row = self.modules_count - 1
        bit_index = 7
        byte_index = 0

        mask_func = util.mask_func(mask_pattern)
        data_len = len(data)

        for col in range(self.modules_count - 1, 0, -2):
            if col <= 6:
                col -= 1  # noqa: PLW2901

            col_range = (col, col - 1)

            while True:
                for c in col_range:
                    if self.modules[row][c] is None:
                        dark = False

                        if byte_index < data_len:
                            dark = ((data[byte_index] >> bit_index) & 1) == 1

                        if mask_func(row, c):
                            dark = not dark

                        self.modules[row][c] = dark
                        bit_index -= 1

                        if bit_index == -1:
                            byte_index += 1
                            bit_index = 7

                row += inc

                if row < 0 or self.modules_count <= row:
                    row -= inc
                    inc = -inc
                    break

    def get_matrix(self) -> list[list[bool]]:
        """Return the QR Code as a multidimensional boolean array.

        The returned matrix includes the quiet-zone border unless you set
        ``self.border = 0`` first.

        Returns:
            A list of lists where each inner list represents one row and
            ``True`` means a dark module, ``False`` means light.
        """
        if self.data_cache is None:
            self.make()

        if not self.border:
            return cast("list[list[bool]]", self.modules)

        width = len(self.modules) + self.border * 2
        code: list[list[bool]] = [[False] * width for _ in range(self.border)]
        x_border = [False] * self.border
        for module in self.modules:
            code.append(x_border + cast("list[bool]", module) + x_border)
        code += [[False] * width for _ in range(self.border)]

        return code

    def active_with_neighbors(self, row: int, col: int) -> ActiveWithNeighbors:
        """Return the 3×3 neighbourhood around *(row, col)*.

        Used by styled drawers that need context-aware rendering.

        Args:
            row: Row index of the centre cell.
            col: Column index of the centre cell.

        Returns:
            :class:`ActiveWithNeighbors` named tuple with 9 boolean values.
        """
        context: list[bool] = []
        for r in range(row - 1, row + 2):
            for c in range(col - 1, col + 2):
                context.append(self.is_constrained(r, c) and bool(self.modules[r][c]))
        return ActiveWithNeighbors(*context)
