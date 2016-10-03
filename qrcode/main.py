from qrcode import constants, exceptions, util
from qrcode.image.base import BaseImage

from collections import defaultdict
import six
from bisect import bisect_left


def make(data=None, **kwargs):
    qr = QRCode(**kwargs)
    qr.add_data(data)
    return qr.make_image()


def _check_version(version):
    if version < 1 or version > 40:
        raise ValueError(
            "Invalid version (was %s, expected 1 to 40)" % version)


def _check_box_size(size):
    if int(size) <= 0:
        raise ValueError(
            "Invalid box size (was %s, expected larger than 0)" % size)


class QRCode:
    def __init__(self, version=None,
                 error_correction=constants.ERROR_CORRECT_M,
                 box_size=50, border=1,
                 image_factory=None,
                 false_color=(255,255,255),
                 true_color=(0,0,0),
                 extended_colors=None,
                 copy_colors_to_ec=False,
                 image_factory_modifiers=None):
        _check_box_size(box_size)
        self.version = version and int(version)
        self.error_correction = int(error_correction)
        self.box_size = int(box_size)
        # Spec says border should be at least four boxes wide, but allow for
        # any (e.g. for producing printable QR codes).
        self.border = int(border)
        self.set_image_factory(image_factory)
        if None == image_factory_modifiers:
            image_factory_modifiers = {}
        self.image_factory_modifiers = image_factory_modifiers
        self.clear()
        self.control_colors = defaultdict(lambda :true_color)
        self.control_colors[True] = true_color
        self.control_colors[False] = false_color
        self.control_colors[0] = false_color
        self.control_colors[None] = false_color
        if extended_colors:
            self.control_colors.update(extended_colors)
        self.copy_colors_to_ec = copy_colors_to_ec

    def set_image_factory(self, image_factory):
        if isinstance(image_factory, str):
            image_factory = image_factory.lower()
            if image_factory == 'pil':
                from qrcode.image.pil import PilImage
                image_factory = PilImage
            elif image_factory == 'svg':
                from qrcode.image.svg import SvgImage
                image_factory = SvgImage
            elif image_factory == 'tty':
                from qrcode.image.tty import TTYImage
                image_factory = TTYImage
            elif image_factory == 'ascii':
                from qrcode.image.ascii import ASCIIImage
                image_factory = ASCIIImage
            else:
                raise Exception("Unknown Image factory %s" % image_factory)
        elif image_factory is None:
            # Use PIL by default
            from qrcode.image.pil import PilImage
            image_factory = PilImage
        else:
            assert issubclass(image_factory, BaseImage)
        self.image_factory = image_factory

    def clear(self):
        """
        Reset the internal data.
        """
        self.modules = None
        self.modules_count = 0
        self.data_cache = None
        self.data_list = []
        self.raw_data = ''
        self.colors = []

    def add_data(self, data, color=None, optimize=True):
        """
        Add data to this QR Code.
        """
        if None == color:
            color = self.control_colors[True]
        if isinstance(data, util.QRData):
            self.data_list.append(data)
            self.raw_data += data.data
            self.colors += [color] * len(data.data)
        else:
            self.raw_data += data
            self.colors += [color] * len(data)
            if optimize:
                self.data_list = util.optimal_data_chunks(self.raw_data)
            else:
                self.data_list.append(util.QRData(data, color=color))
        self.data_cache = None

    def make(self, fit=True):
        """
        Compile the data into a QR Code array.

        :param fit: If ``True`` (or if a size has not been provided), find the
            best fit for the data to avoid data overflow errors.
        """
        if fit or (self.version is None):
            self.best_fit(start=self.version)
        self.makeImpl(False, self.best_mask_pattern())

    def makeImpl(self, test, mask_pattern, use_colors=True):
        _check_version(self.version)
        self.modules_count = self.version * 4 + 17
        self.modules = [None] * self.modules_count

        for row in range(self.modules_count):

            self.modules[row] = [None] * self.modules_count

            for col in range(self.modules_count):
                self.modules[row][col] = None   # (col + row) % 3

        self.setup_position_probe_pattern(0, 0, use_colors=use_colors)
        self.setup_position_probe_pattern(self.modules_count - 7, 0, use_colors=use_colors)
        self.setup_position_probe_pattern(0, self.modules_count - 7, use_colors=use_colors)
        self.setup_position_adjust_pattern(use_colors=use_colors)
        self.setup_timing_pattern(use_colors=use_colors)
        self.setup_type_info(test, mask_pattern, use_colors=use_colors)

        if self.version >= 7:
            self.setup_type_number(test, use_colors=use_colors)

        if self.data_cache is None:
            self.data_cache = util.create_data(
                                    self.version,
                                    self.error_correction,
                                    self.data_list,
                                    self.colors,
                                    self.control_colors,
                                    copy_colors_to_ec=self.copy_colors_to_ec)
        self.map_data(self.data_cache, mask_pattern, use_colors=use_colors)

    def get_false_and_true_colors(self, color_index, use_colors=True):
        if use_colors:
            true_color = self.control_colors[color_index]
            false_color = self.control_colors[False]
        else:
            true_color = True
            false_color = False
        return (false_color, true_color)

    def setup_position_probe_pattern(self, row, col, use_colors=True):
        false_color, true_color = self.get_false_and_true_colors('prob', use_colors=use_colors)

        for r in range(-1, 8):

            if row + r <= -1 or self.modules_count <= row + r:
                continue

            for c in range(-1, 8):

                if col + c <= -1 or self.modules_count <= col + c:
                    continue

                if (0 <= r and r <= 6 and (c == 0 or c == 6)
                        or (0 <= c and c <= 6 and (r == 0 or r == 6))
                        or (2 <= r and r <= 4 and 2 <= c and c <= 4)):
                    self.modules[row + r][col + c] = true_color
                else:
                    self.modules[row + r][col + c] = false_color

    def best_fit(self, start=None):
        """
        Find the minimum size required to fit in the data.
        """
        if start is None:
            start = 1
        _check_version(start)

        # Corresponds to the code in util.create_data, except we don't yet know
        # version, so optimistically assume start and check later
        mode_sizes = util.mode_sizes_for_version(start)
        buffer = util.BitBuffer()
        for data in self.data_list:
            buffer.put(data.mode, 4, None)
            buffer.put(len(data), mode_sizes[data.mode], None)
            data.write_to_buffer(buffer, None)

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
            self.makeImpl(True, i, use_colors=False)

            lost_point = util.lost_point(self.modules)

            if i == 0 or min_lost_point > lost_point:
                min_lost_point = lost_point
                pattern = i

        return pattern

    def make_image(self, **kwargs):
        """
        Make an image from the QR Code data.

        If the data has not been compiled yet, make it first.
        """
        _check_box_size(self.box_size)
        if self.data_cache is None:
            self.make()

        im = self.image_factory(
            self.border, self.modules_count, self.box_size, **self.image_factory_modifiers)
        for r in range(self.modules_count):
            for c in range(self.modules_count):
                im.drawrect(r, c, self.modules[r][c])
        return im

    def setup_timing_pattern(self, use_colors=True):
        false_color, true_color = self.get_false_and_true_colors('timing', use_colors=use_colors)

        for r in range(8, self.modules_count - 8):
            if self.modules[r][6] is not None:
                continue
            if not (r % 2):
                self.modules[r][6] = true_color
            else:
                self.modules[r][6] = false_color

        for c in range(8, self.modules_count - 8):
            if self.modules[6][c] is not None:
                continue
            if not (c % 2):
                self.modules[6][c] = true_color
            else:
                self.modules[6][c] = false_color

    def setup_position_adjust_pattern(self, use_colors):
        false_color, true_color = self.get_false_and_true_colors('prob', use_colors=use_colors)
        pos = util.pattern_position(self.version)

        for i in range(len(pos)):
            for j in range(len(pos)):

                row = pos[i]
                col = pos[j]

                if self.modules[row][col] is not None:
                    continue

                for r in range(-2, 3):
                    for c in range(-2, 3):
                        if (r == -2 or r == 2 or c == -2 or c == 2 or (r == 0 and c == 0)):
                            self.modules[row + r][col + c] = true_color
                        else:
                            self.modules[row + r][col + c] = false_color

    def setup_type_number(self, test, use_colors=True):
        false_color, true_color = self.get_false_and_true_colors('type', use_colors=use_colors)
        colors = {False:false_color, True:true_color}
        bits = util.BCH_type_number(self.version)

        for i in range(18):
            mod = colors[bool(not test and ((bits >> i) & 1) == 1)]
            self.modules[i // 3][i % 3 + self.modules_count - 8 - 3] = mod

        for i in range(18):
            mod = colors[bool(not test and ((bits >> i) & 1) == 1)]
            self.modules[i % 3 + self.modules_count - 8 - 3][i // 3] = mod

    def setup_type_info(self, test, mask_pattern, use_colors=True):
        false_color, true_color = self.get_false_and_true_colors('type', use_colors=use_colors)
        colors = {False:false_color, True:true_color}
        data = (self.error_correction << 3) | mask_pattern
        bits = util.BCH_type_info(data)

        # vertical
        for i in range(15):

            mod = colors[bool(not test and ((bits >> i) & 1) == 1)]

            if i < 6:
                self.modules[i][8] = mod
            elif i < 8:
                self.modules[i + 1][8] = mod
            else:
                self.modules[self.modules_count - 15 + i][8] = mod

        # horizontal
        for i in range(15):

            mod = colors[bool((not test and ((bits >> i) & 1) == 1))]

            if i < 8:
                self.modules[8][self.modules_count - i - 1] = mod
            elif i < 9:
                self.modules[8][15 - i - 1 + 1] = mod
            else:
                self.modules[8][15 - i - 1] = mod

        # fixed module
        self.modules[self.modules_count - 8][8] = colors[bool(not test)]

    def map_data(self, data, mask_pattern, use_colors=True):
        inc = -1
        row = self.modules_count - 1
        bit_index = 0
        false_color, true_color = self.get_false_and_true_colors('padding', use_colors)

        mask_func = util.mask_func(mask_pattern)

        for col in six.moves.xrange(self.modules_count - 1, 0, -2):

            if col <= 6:
                col -= 1

            col_range = (col, col-1)

            while row >= 0 and self.modules_count > row:
                for c in col_range:
                    if self.modules[row][c] is None:
                        if bit_index < len(data):
                            bit = data[bit_index]
                            value = bit[0]
                            color = bit[1]
                        else:
                            value = False
                            color = true_color

                        if mask_func(row, c):
                            value = not value

                        if use_colors:
                            if value:
                                self.modules[row][c] = color
                            else:
                                self.modules[row][c] = false_color
                        else:
                            self.modules[row][c] = value

                        bit_index += 1

                row += inc
            row -= inc
            inc = -inc

    def get_matrix(self):
        """
        Return the QR Code as a multidimensonal array, including the border.

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
