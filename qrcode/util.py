import re
import math

from qrcode import base, exceptions

# QR encoding modes.
MODE_NUMBER = 1 << 0
MODE_ALPHA_NUM = 1 << 1
MODE_8BIT_BYTE = 1 << 2
MODE_KANJI = 1 << 3

# Encoding mode sizes.
MODE_SIZE_SMALL = {
    MODE_NUMBER: 10,
    MODE_ALPHA_NUM: 9,
    MODE_8BIT_BYTE: 8,
    MODE_KANJI: 8,
}
MODE_SIZE_MEDIUM = {
    MODE_NUMBER: 12,
    MODE_ALPHA_NUM: 11,
    MODE_8BIT_BYTE: 16,
    MODE_KANJI: 10,
}
MODE_SIZE_LARGE = {
    MODE_NUMBER: 14,
    MODE_ALPHA_NUM: 13,
    MODE_8BIT_BYTE: 16,
    MODE_KANJI: 12,
}

ALPHA_NUM = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'

# The number of bits for numeric delimited data lengths.
NUMBER_LENGTH = {3: 10, 2: 7, 1: 4}

PATTERN_POSITION_TABLE = [
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
    [6, 30, 58, 86, 114, 142, 170]
]

G15 = ((1 << 10) | (1 << 8) | (1 << 5) | (1 << 4) | (1 << 2) | (1 << 1) |
    (1 << 0))
G18 = ((1 << 12) | (1 << 11) | (1 << 10) | (1 << 9) | (1 << 8) | (1 << 5) |
    (1 << 2) | (1 << 0))
G15_MASK = (1 << 14) | (1 << 12) | (1 << 10) | (1 << 4) | (1 << 1)

PAD0 = 0xEC
PAD1 = 0x11


def BCH_type_info(data):
        d = data << 10
        while BCH_digit(d) - BCH_digit(G15) >= 0:
            d ^= (G15 << (BCH_digit(d) - BCH_digit(G15)))

        return ((data << 10) | d) ^ G15_MASK


def BCH_type_number(data):
    d = data << 12
    while BCH_digit(d) - BCH_digit(G18) >= 0:
        d ^= (G18 << (BCH_digit(d) - BCH_digit(G18)))
    return (data << 12) | d


def BCH_digit(data):
    digit = 0
    while data != 0:
        digit += 1
        data >>= 1
    return digit


def pattern_position(version):
    return PATTERN_POSITION_TABLE[version - 1]


def mask_func(pattern):
    """
    Return the mask function for the given mask pattern.
    """
    if pattern == 0:   # 000
        return lambda i, j: (i + j) % 2 == 0
    if pattern == 1:   # 001
        return lambda i, j: i % 2 == 0
    if pattern == 2:   # 010
        return lambda i, j: j % 3 == 0
    if pattern == 3:   # 011
        return lambda i, j: (i + j) % 3 == 0
    if pattern == 4:   # 100
        return lambda i, j: (math.floor(i / 2) + math.floor(j / 3)) % 2 == 0
    if pattern == 5:  # 101
        return lambda i, j: (i * j) % 2 + (i * j) % 3 == 0
    if pattern == 6:  # 110
        return lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0
    if pattern == 7:  # 111
        return lambda i, j: ((i * j) % 3 + (i + j) % 2) % 2 == 0
    raise TypeError("Bad mask pattern: " + pattern)


def length_in_bits(mode, version):
    if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE,
            MODE_KANJI):
        raise TypeError("Invalid mode (%s)" % mode)

    if version < 1 or version > 40:
        raise ValueError("Invalid version (was %s, expected 1 to 40)" %
            version)

    if version < 10:
        mode_size = MODE_SIZE_SMALL
    elif version < 27:
        mode_size = MODE_SIZE_MEDIUM
    else:
        mode_size = MODE_SIZE_LARGE

    return mode_size[mode]


def lost_point(modules):
    modules_count = len(modules)

    lost_point = 0

    # LEVEL1

    for row in range(modules_count):

        for col in range(modules_count):

            sameCount = 0
            dark = modules[row][col]

            for r in range(-1, 2):

                if row + r < 0 or modules_count <= row + r:
                    continue

                for c in range(-1, 2):

                    if col + c < 0 or modules_count <= col + c:
                        continue
                    if r == 0 and c == 0:
                        continue

                    if dark == modules[row + r][col + c]:
                        sameCount += 1
            if sameCount > 5:
                lost_point += (3 + sameCount - 5)

    # LEVEL2

    for row in range(modules_count - 1):
        for col in range(modules_count - 1):
            count = 0
            if modules[row][col]:
                count += 1
            if modules[row + 1][col]:
                count += 1
            if modules[row][col + 1]:
                count += 1
            if modules[row + 1][col + 1]:
                count += 1
            if count == 0 or count == 4:
                lost_point += 3

    # LEVEL3

    for row in range(modules_count):
        for col in range(modules_count - 6):
            if (modules[row][col]
                    and not modules[row][col + 1]
                    and modules[row][col + 2]
                    and modules[row][col + 3]
                    and modules[row][col + 4]
                    and not modules[row][col + 5]
                    and modules[row][col + 6]):
                lost_point += 40

    for col in range(modules_count):
        for row in range(modules_count - 6):
            if (modules[row][col]
                    and not modules[row + 1][col]
                    and modules[row + 2][col]
                    and modules[row + 3][col]
                    and modules[row + 4][col]
                    and not modules[row + 5][col]
                    and modules[row + 6][col]):
                lost_point += 40

    # LEVEL4

    darkCount = 0

    for col in range(modules_count):
        for row in range(modules_count):
            if modules[row][col]:
                darkCount += 1

    ratio = abs(100 * darkCount / modules_count / modules_count - 50) / 5
    lost_point += ratio * 10

    return lost_point


class QRData:
    """
    Data held in a QR compatible format.

    Doesn't currently handle KANJI.
    """

    def __init__(self, data, mode=None):
        """
        If ``mode`` isn't provided, the most compact QR data type possible is
        chosen.
        """
        # Convert data to a (utf-8 encoded) byte-string.
        if not isinstance(data, basestring):
            try:
                data = str(data)
            except UnicodeEncodeError:
                data = unicode(data)
        if isinstance(data, unicode):
            data = data.encode('utf-8')

        if data.isdigit():
            auto_mode = MODE_NUMBER
        elif re.match('^[%s]*$' % re.escape(ALPHA_NUM), data):
            auto_mode = MODE_ALPHA_NUM
        else:
            auto_mode = MODE_8BIT_BYTE

        if mode is None:
            self.mode = auto_mode
        else:
            if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE):
                raise TypeError("Invalid mode (%s)" % mode)
            if mode < auto_mode:
                raise ValueError("Provided data can not be represented in "
                    "mode %s" % mode)
            self.mode = mode

        self.data = data

    def __len__(self):
        return len(self.data)

    def write(self, buffer):
        if self.mode == MODE_NUMBER:
            for i in xrange(0, len(self.data), 3):
                chars = self.data[i:i + 3]
                bit_length = NUMBER_LENGTH[len(chars)]
                buffer.put(int(chars), bit_length)
        elif self.mode == MODE_ALPHA_NUM:
            for i in xrange(0, len(self.data), 2):
                chars = self.data[i:i + 2]
                if len(chars) > 1:
                    buffer.put(ALPHA_NUM.find(chars[0]) * 45 +
                        ALPHA_NUM.find(chars[1]), 11)
                else:
                    buffer.put(ALPHA_NUM.find(chars), 6)
        else:
            for c in self.data:
                buffer.put(ord(c), 8)

    def __repr__(self):
        return self.data


class BitBuffer:

    def __init__(self):
        self.buffer = []
        self.length = 0

    def __repr__(self):
        return ".".join([str(n) for n in self.buffer])

    def get(self, index):
        buf_index = math.floor(index / 8)
        return ((self.buffer[buf_index] >> (7 - index % 8)) & 1) == 1

    def put(self, num, length):
        for i in range(length):
            self.put_bit(((num >> (length - i - 1)) & 1) == 1)

    def __len__(self):
        return self.length

    def put_bit(self, bit):
        buf_index = self.length // 8
        if len(self.buffer) <= buf_index:
            self.buffer.append(0)
        if bit:
            self.buffer[buf_index] |= (0x80 >> (self.length % 8))
        self.length += 1


def create_bytes(buffer, rs_blocks):
    offset = 0

    maxDcCount = 0
    maxEcCount = 0

    dcdata = [0] * len(rs_blocks)
    ecdata = [0] * len(rs_blocks)

    for r in range(len(rs_blocks)):

        dcCount = rs_blocks[r].data_count
        ecCount = rs_blocks[r].total_count - dcCount

        maxDcCount = max(maxDcCount, dcCount)
        maxEcCount = max(maxEcCount, ecCount)

        dcdata[r] = [0] * dcCount

        for i in range(len(dcdata[r])):
            dcdata[r][i] = 0xff & buffer.buffer[i + offset]
        offset += dcCount

        # Get error correction polynomial.
        rsPoly = base.Polynomial([1], 0)
        for i in range(ecCount):
            rsPoly = rsPoly * base.Polynomial([1, base.gexp(i)], 0)

        rawPoly = base.Polynomial(dcdata[r], len(rsPoly) - 1)

        modPoly = rawPoly % rsPoly
        ecdata[r] = [0] * (len(rsPoly) - 1)
        for i in range(len(ecdata[r])):
            modIndex = i + len(modPoly) - len(ecdata[r])
            if (modIndex >= 0):
                ecdata[r][i] = modPoly[modIndex]
            else:
                ecdata[r][i] = 0

    totalCodeCount = 0
    for rs_block in rs_blocks:
        totalCodeCount += rs_block.total_count

    data = [None] * totalCodeCount
    index = 0

    for i in range(maxDcCount):
        for r in range(len(rs_blocks)):
            if i < len(dcdata[r]):
                data[index] = dcdata[r][i]
                index += 1

    for i in range(maxEcCount):
        for r in range(len(rs_blocks)):
            if i < len(ecdata[r]):
                data[index] = ecdata[r][i]
                index += 1

    return data


def create_data(version, error_correction, data_list):

    rs_blocks = base.rs_blocks(version, error_correction)

    buffer = BitBuffer()

    for data in data_list:
        buffer.put(data.mode, 4)
        buffer.put(len(data),
            length_in_bits(data.mode, version))
        data.write(buffer)

    # calc num max data.
    total_data_count = 0
    for block in rs_blocks:
        total_data_count += block.data_count

    if len(buffer) > total_data_count * 8:
        raise exceptions.DataOverflowError("Code length overflow. Data size "
            "(%s) > size available (%s)" % (len(buffer), total_data_count * 8))

    # end code
    if len(buffer) + 4 <= total_data_count * 8:
        buffer.put(0, 4)

    # padding
    while len(buffer) % 8:
        buffer.put_bit(False)

    # padding
    while True:
        if len(buffer) >= total_data_count * 8:
            break
        buffer.put(PAD0, 8)

        if len(buffer) >= total_data_count * 8:
            break
        buffer.put(PAD1, 8)

    return create_bytes(buffer, rs_blocks)
