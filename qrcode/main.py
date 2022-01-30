from qrcode import constants, exceptions, util
from qrcode.image.base import BaseImage

import sys
from bisect import bisect_left

# Cache modules generated just based on the QR Code version
precomputed_qr_blanks = {}

def make(data=None, **kwargs):
    qr = QRCode(**kwargs)
    qr.add_data(data)
    return qr.make_image()


def _check_box_size(size):
    if int(size) <= 0:
        raise ValueError(
            f"Invalid box size (was {size}, expected larger than 0)")

def _check_border(size):
    if int(size) < 0:
        raise ValueError("Invalid border value (was %s, expected 0 or larger than that)" % size)


def _check_mask_pattern(mask_pattern):
    if mask_pattern is None:
        return
    if not isinstance(mask_pattern, int):
        raise TypeError(
            f"Invalid mask pattern (was {type(mask_pattern)}, expected int)")
    if mask_pattern < 0 or mask_pattern > 7:
        raise ValueError(
            f"Mask pattern should be in range(8) (got {mask_pattern})")

def copy_2d_array(x):
    return [row[:] for row in x]

class QRCode:

    def __init__(self, version=None,
                 error_correction=constants.ERROR_CORRECT_M,
                 box_size=10, border=4,
                 image_factory=None,
                 mask_pattern=None):
        _check_box_size(box_size)
        _check_border(border)
        self.version = version and int(version)
        self.error_correction = int(error_correction)
        self.box_size = int(box_size)
        # Spec says border should be at least four boxes wide, but allow for
        # any (e.g. for producing printable QR codes).
        self.border = int(border)
        self.mask_pattern = mask_pattern
        self.image_factory = image_factory
        if image_factory is not None:
            assert issubclass(image_factory, BaseImage)
        self.clear()

    @property
    def mask_pattern(self):
        return self._mask_pattern

    @mask_pattern.setter
    def mask_pattern(self, pattern):
        _check_mask_pattern(pattern)
        self._mask_pattern = pattern

    def clear(self):
        """
        Reset the internal data.
        """
        self.modules = None
        self.modules_count = 0
        self.data_cache = None
        self.data_list = []

    def add_data(self, data, optimize=20):
        """
        Add data to this QR Code.

        :param optimize: Data will be split into multiple chunks to optimize
            the QR size by finding to more compressed modes of at least this
            length. Set to ``0`` to avoid optimizing at all.
        """
        if isinstance(data, util.QRData):
            self.data_list.append(data)
        elif optimize:
            self.data_list.extend(
                util.optimal_data_chunks(data, minimum=optimize))
        else:
            self.data_list.append(util.QRData(data))
        self.data_cache = None

    def make(self, fit=True):
        """
        Compile the data into a QR Code array.

        :param fit: If ``True`` (or if a size has not been provided), find the
            best fit for the data to avoid data overflow errors.
        """
        if fit or (self.version is None):
            self.best_fit(start=self.version)
        if self.mask_pattern is None:
            self.makeImpl(False, self.best_mask_pattern())
        else:
            self.makeImpl(False, self.mask_pattern)

    def makeImpl(self, test, mask_pattern):
        util.check_version(self.version)
        self.modules_count = self.version * 4 + 17

        if self.version in precomputed_qr_blanks:
            self.modules = copy_2d_array(precomputed_qr_blanks[self.version])
        else:
            self.modules = [None] * self.modules_count

            for row in range(self.modules_count):
                self.modules[row] = [None] * self.modules_count

            self.setup_position_probe_pattern(0, 0)
            self.setup_position_probe_pattern(self.modules_count - 7, 0)
            self.setup_position_probe_pattern(0, self.modules_count - 7)
            self.setup_position_adjust_pattern()
            self.setup_timing_pattern()

            precomputed_qr_blanks[self.version] = copy_2d_array(self.modules)

        self.setup_type_info(test, mask_pattern)

        if self.version >= 7:
            self.setup_type_number(test)

        if self.data_cache is None:
            self.data_cache = util.create_data(
                self.version, self.error_correction, self.data_list)
        self.map_data(self.data_cache, mask_pattern)

    def setup_position_probe_pattern(self, row, col):
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

    def best_fit(self, start=None):
        """
        Find the minimum size required to fit in the data.
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
        self.version = bisect_left(util.BIT_LIMIT_TABLE[self.error_correction],
                                   needed_bits, start)
        if self.version == 41:
            raise exceptions.DataOverflowError()

        # Now check whether we need more bits for the mode sizes, recursing if
        # our guess was too low
        if mode_sizes is not util.mode_sizes_for_version(self.version):
            self.best_fit(start=self.version)
        return self.version

    def best_mask_pattern(self):
        """
        Find the most efficient mask pattern.
        """
        min_lost_point = 0
        pattern = 0

        for i in range(8):
            self.makeImpl(True, i)

            lost_point = util.lost_point(self.modules)

            if i == 0 or min_lost_point > lost_point:
                min_lost_point = lost_point
                pattern = i

        return pattern

    def print_tty(self, out=None):
        """
        Output the QR Code only using TTY colors.
        If the data has not been compiled yet, make it first.
        """
        if out is None:
            import sys
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

    def print_ascii(self, out=None, tty=False, invert=False, border=None, raw=False, fg=None, bg=None):
        """
        Output the QR Code using ASCII box drawing characters.

        :param tty: use fixed TTY color codes (black and white color-scheme)
        :param invert: invert the ASCII characters (solid <-> transparent)
        :param border: width of border around QR code
        :param raw: Write bytes to out
        :param fg: The X part of the ANSI code \\x1b30m
        """
        if fg is None:
            _setfg = '\x1b[38;5;255m'
        elif isinstance(fg, int):
            _setfg='\x1b[' + str(fg%8+30) + (";1" * (fg//8)) + 'm'
        else:
            _setfg = fg

        if bg is None:
            _setbg = '\x1b[48;5;232m'
        elif isinstance(bg, int):
            _setbg='\x1b[' + str(bg%8+40) + (";1" * (bg//8)) + 'm'
        else:
            _setbg = bg

        _resetColors = '\x1b[0m'
        _newline = '\n'

        if out is None:
            if raw:
                out = sys.stdout.buffer
            else:
                out = sys.stdout

        if border is None:
            border = self.border

        if raw:
            _setbg = _setbg.encode()
            _setfg = _setfg.encode()
            _resetColors = _resetColors.encode()
            _newline = _newline.encode()

        if self.data_cache is None:
            self.make()

        modcount = self.modules_count
        codes = [bytes((code,))
                 for code in (219, 220, 223, 255)]
        if not raw:
            codes=[code.decode('cp437')
                for code in codes]
        if invert:
            codes.reverse()

        def get_module(x, y):
            """
            Find which halves of the box-drawing character at a position need to be filled

            :param x: The vertical   position of the output character
            :param y: The horizontal position of the output character
            :returns: A number from 0 to 3 for neither, top, bottom, and both halves respectively
            """
            if (invert and border and
                    max(x, y) >= modcount+border):
                return 0
            if not invert and x >= modcount+border:
                # Don't fill the bottom half of the bottom row
                return 1
            if min(x, y) < 0 or max(x, y) >= modcount:
                return 0
            return self.modules[x][y]

        for r in range(-border, modcount+border, 2):
            if r > -border:
                # Don't write an extra newline at the end
                out.write(_newline)

            if tty or fg is not None:
                # ANSI stuff to set output color
                out.write(_setfg)
            if tty or bg is not None:
                out.write(_setbg)
            for c in range(-border, modcount+border):
                pos = get_module(r, c) + (get_module(r+1, c) << 1)
                out.write(codes[pos])
            if tty or fg is not None or bg is not None:
                out.write(_resetColors)
        out.flush()

    def make_image(self, image_factory=None, **kwargs):
        """
        Make an image from the QR Code data.

        If the data has not been compiled yet, make it first.
        """
        _check_box_size(self.box_size)
        if self.data_cache is None:
            self.make()

        if image_factory is not None:
            assert issubclass(image_factory, BaseImage)
        else:
            image_factory = self.image_factory
            if image_factory is None:
                # Use PIL by default
                from qrcode.image.pil import PilImage
                image_factory = PilImage

        im = image_factory(
            self.border, self.modules_count, self.box_size, **kwargs)

        for r in range(self.modules_count):
            for c in range(self.modules_count):
                if im.needs_context:
                    im.drawrect_context(r, c, self.modules[r][c], self.get_module_context(r,c))
                elif self.modules[r][c]:
                    im.drawrect(r,c)
        if im.needs_processing:
            im.process()

        return im

    # return true if and only if (row, col) is in the module
    def is_constrained(self, row, col):
        return row >= 0 and row < len(self.modules) and col >= 0 and col < len(self.modules[row])

    def get_module_context(self, row, col):
        context = []

        for r in range(row-1,row + 2):
            for c in range(col - 1, col + 2):
                if r != row or c != col:
                    context.append(self.is_constrained(r,c) and self.modules[r][c])
        return context

    def setup_timing_pattern(self):
        for r in range(8, self.modules_count - 8):
            if self.modules[r][6] is not None:
                continue
            self.modules[r][6] = (r % 2 == 0)

        for c in range(8, self.modules_count - 8):
            if self.modules[6][c] is not None:
                continue
            self.modules[6][c] = (c % 2 == 0)

    def setup_position_adjust_pattern(self):
        pos = util.pattern_position(self.version)

        for i in range(len(pos)):

            row = pos[i]

            for j in range(len(pos)):

                col = pos[j]

                if self.modules[row][col] is not None:
                    continue

                for r in range(-2, 3):

                    for c in range(-2, 3):

                        if (r == -2 or r == 2 or c == -2 or c == 2 or
                                (r == 0 and c == 0)):
                            self.modules[row + r][col + c] = True
                        else:
                            self.modules[row + r][col + c] = False

    def setup_type_number(self, test):
        bits = util.BCH_type_number(self.version)

        for i in range(18):
            mod = (not test and ((bits >> i) & 1) == 1)
            self.modules[i // 3][i % 3 + self.modules_count - 8 - 3] = mod

        for i in range(18):
            mod = (not test and ((bits >> i) & 1) == 1)
            self.modules[i % 3 + self.modules_count - 8 - 3][i // 3] = mod

    def setup_type_info(self, test, mask_pattern):
        data = (self.error_correction << 3) | mask_pattern
        bits = util.BCH_type_info(data)

        # vertical
        for i in range(15):

            mod = (not test and ((bits >> i) & 1) == 1)

            if i < 6:
                self.modules[i][8] = mod
            elif i < 8:
                self.modules[i + 1][8] = mod
            else:
                self.modules[self.modules_count - 15 + i][8] = mod

        # horizontal
        for i in range(15):

            mod = (not test and ((bits >> i) & 1) == 1)

            if i < 8:
                self.modules[8][self.modules_count - i - 1] = mod
            elif i < 9:
                self.modules[8][15 - i - 1 + 1] = mod
            else:
                self.modules[8][15 - i - 1] = mod

        # fixed module
        self.modules[self.modules_count - 8][8] = (not test)

    def map_data(self, data, mask_pattern):
        inc = -1
        row = self.modules_count - 1
        bitIndex = 7
        byteIndex = 0

        mask_func = util.mask_func(mask_pattern)

        data_len = len(data)

        for col in range(self.modules_count - 1, 0, -2):

            if col <= 6:
                col -= 1

            col_range = (col, col-1)

            while True:

                for c in col_range:

                    if self.modules[row][c] is None:

                        dark = False

                        if byteIndex < data_len:
                            dark = (((data[byteIndex] >> bitIndex) & 1) == 1)

                        if mask_func(row, c):
                            dark = not dark

                        self.modules[row][c] = dark
                        bitIndex -= 1

                        if bitIndex == -1:
                            byteIndex += 1
                            bitIndex = 7

                row += inc

                if row < 0 or self.modules_count <= row:
                    row -= inc
                    inc = -inc
                    break

    def get_matrix(self):
        """
        Return the QR Code as a multidimensional array, including the border.

        To return the array without a border, set ``self.border`` to 0 first.
        """
        if self.data_cache is None:
            self.make()

        if not self.border:
            return self.modules

        width = len(self.modules) + self.border*2
        code = [[False]*width] * self.border
        x_border = [False]*self.border
        for module in self.modules:
            code.append(x_border + module + x_border)
        code += [[False]*width] * self.border

        return code
