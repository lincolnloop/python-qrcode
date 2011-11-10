import math

from qrcode import constants

EXP_TABLE = list(range(256))

LOG_TABLE = list(range(256))

for i in range(8):
    EXP_TABLE[i] = 1 << i

for i in range(8, 256):
    EXP_TABLE[i] = (EXP_TABLE[i - 4] ^ EXP_TABLE[i - 5] ^ EXP_TABLE[i - 6] ^
        EXP_TABLE[i - 8])

for i in range(255):
    LOG_TABLE[EXP_TABLE[i]] = i


class QR8bitByte:

    def __init__(self, data):
        self.mode = QRMode.MODE_8BIT_BYTE
        self.data = data

    def getLength(self):
        return len(self.data)

    def write(self, buffer):
        for c in self.data:
            # not JIS ...
            buffer.put(ord(c), 8)

    def __repr__(self):
        return self.data


class QRMode:
    MODE_NUMBER = 1 << 0
    MODE_ALPHA_NUM = 1 << 1
    MODE_8BIT_BYTE = 1 << 2
    MODE_KANJI = 1 << 3


class QRUtil(object):
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

    @staticmethod
    def getBCHTypeInfo(data):
        d = data << 10
        while (QRUtil.getBCHDigit(d) - QRUtil.getBCHDigit(QRUtil.G15) >= 0):
            d ^= (QRUtil.G15 <<
                (QRUtil.getBCHDigit(d) - QRUtil.getBCHDigit(QRUtil.G15)))

        return ((data << 10) | d) ^ QRUtil.G15_MASK

    @staticmethod
    def getBCHTypeNumber(data):
        d = data << 12
        while (QRUtil.getBCHDigit(d) - QRUtil.getBCHDigit(QRUtil.G18) >= 0):
            d ^= (QRUtil.G18 <<
                (QRUtil.getBCHDigit(d) - QRUtil.getBCHDigit(QRUtil.G18)))
        return (data << 12) | d

    @staticmethod
    def getBCHDigit(data):
        digit = 0
        while (data != 0):
            digit += 1
            data >>= 1
        return digit

    @staticmethod
    def getPatternPosition(typeNumber):
        return QRUtil.PATTERN_POSITION_TABLE[typeNumber - 1]

    @staticmethod
    def getMask(maskPattern, i, j):
        if maskPattern == 0:   # 000
            return (i + j) % 2 == 0
        if maskPattern == 1:   # 001
            return i % 2 == 0
        if maskPattern == 2:   # 010
            return j % 3 == 0
        if maskPattern == 3:   # 011
            return (i + j) % 3 == 0
        if maskPattern == 4:   # 100
            return (math.floor(i / 2) + math.floor(j / 3)) % 2 == 0
        if maskPattern == 5:  # 101
            return (i * j) % 2 + (i * j) % 3 == 0
        if maskPattern == 6:  # 110
            return ((i * j) % 2 + (i * j) % 3) % 2 == 0
        if maskPattern == 7:  # 111
            return ((i * j) % 3 + (i + j) % 2) % 2 == 0
        raise Exception("bad maskPattern:" + maskPattern)

    @staticmethod
    def getErrorCorrectPolynomial(errorCorrectLength):
        a = QRPolynomial([1], 0)
        for i in range(errorCorrectLength):
            a = a.multiply(QRPolynomial([1, QRMath.gexp(i)], 0))
        return a

    @staticmethod
    def getLengthInBits(mode, type):

        if 1 <= type and type < 10:

            # 1 - 9

            if mode == QRMode.MODE_NUMBER:
                return 10
            if mode == QRMode.MODE_ALPHA_NUM:
                return 9
            if mode == QRMode.MODE_8BIT_BYTE:
                return 8
            if mode == QRMode.MODE_KANJI:
                return 8
            raise Exception("mode:" + mode)

        elif (type < 27):

            # 10 - 26

            if mode == QRMode.MODE_NUMBER:
                return 12
            if mode == QRMode.MODE_ALPHA_NUM:
                return 11
            if mode == QRMode.MODE_8BIT_BYTE:
                return 16
            if mode == QRMode.MODE_KANJI:
                return 10
            raise Exception("mode:" + mode)

        elif (type < 41):

            # 27 - 40

            if mode == QRMode.MODE_NUMBER:
                return 14
            if mode == QRMode.MODE_ALPHA_NUM:
                return 13
            if mode == QRMode.MODE_8BIT_BYTE:
                return 16
            if mode == QRMode.MODE_KANJI:
                return 12
            raise Exception("mode:" + mode)

        raise Exception("type:" + type)

    @staticmethod
    def getLostPoint(qrCode):
        moduleCount = qrCode.moduleCount

        lostPoint = 0

        # LEVEL1

        for row in range(moduleCount):

            for col in range(moduleCount):

                sameCount = 0
                dark = qrCode.modules[row][col]

                for r in range(-1, 2):

                    if (row + r < 0 or moduleCount <= row + r):
                        continue

                    for c in range(-1, 2):

                        if (col + c < 0 or moduleCount <= col + c):
                            continue
                        if (r == 0 and c == 0):
                            continue

                        if (dark == qrCode.modules[row + r][col + c]):
                            sameCount += 1
                if (sameCount > 5):
                    lostPoint += (3 + sameCount - 5)

        # LEVEL2

        for row in range(moduleCount - 1):
            for col in range(moduleCount - 1):
                count = 0
                if (qrCode.modules[row][col]):
                    count += 1
                if (qrCode.modules[row + 1][col]):
                    count += 1
                if (qrCode.modules[row][col + 1]):
                    count += 1
                if (qrCode.modules[row + 1][col + 1]):
                    count += 1
                if (count == 0 or count == 4):
                    lostPoint += 3

        # LEVEL3

        for row in range(moduleCount):
            for col in range(moduleCount - 6):
                if (qrCode.modules[row][col]
                        and not qrCode.modules[row][col + 1]
                        and qrCode.modules[row][col + 2]
                        and qrCode.modules[row][col + 3]
                        and qrCode.modules[row][col + 4]
                        and not qrCode.modules[row][col + 5]
                        and qrCode.modules[row][col + 6]):
                    lostPoint += 40

        for col in range(moduleCount):
            for row in range(moduleCount - 6):
                if (qrCode.modules[row][col]
                        and not qrCode.modules[row + 1][col]
                        and qrCode.modules[row + 2][col]
                        and qrCode.modules[row + 3][col]
                        and qrCode.modules[row + 4][col]
                        and not qrCode.modules[row + 5][col]
                        and qrCode.modules[row + 6][col]):
                    lostPoint += 40

        # LEVEL4

        darkCount = 0

        for col in range(moduleCount):
            for row in range(moduleCount):
                if (qrCode.modules[row][col]):
                    darkCount += 1

        ratio = abs(100 * darkCount / moduleCount / moduleCount - 50) / 5
        lostPoint += ratio * 10

        return lostPoint


class QRMath:

    @staticmethod
    def glog(n):
        if (n < 1):
            raise Exception("glog(" + n + ")")
        return LOG_TABLE[n]

    @staticmethod
    def gexp(n):
        while n < 0:
            n += 255
        while n >= 256:
            n -= 255
        return EXP_TABLE[n]


class QRPolynomial:

    def __init__(self, num, shift):

        if (len(num) == 0):
            raise Exception(num.length + "/" + shift)

        offset = 0

        while offset < len(num) and num[offset] == 0:
            offset += 1

        self.num = [0 for x in range(len(num) - offset + shift)]
        for i in range(len(num) - offset):
            self.num[i] = num[i + offset]

    def get(self, index):

        return self.num[index]

    def getLength(self):
        return len(self.num)

    def multiply(self, e):
        num = [0 for x in range(self.getLength() + e.getLength() - 1)]

        for i in range(self.getLength()):
            for j in range(e.getLength()):
                num[i + j] ^= QRMath.gexp(QRMath.glog(self.get(i)) +
                    QRMath.glog(e.get(j)))

        return QRPolynomial(num, 0)

    def mod(self, e):

        if (self.getLength() - e.getLength() < 0):
            return self

        ratio = QRMath.glog(self.get(0)) - QRMath.glog(e.get(0))

        num = [0 for x in range(self.getLength())]

        for i in range(self.getLength()):
            num[i] = self.get(i)

        for i in range(e.getLength()):
            num[i] ^= QRMath.gexp(QRMath.glog(e.get(i)) + ratio)

        # recursive call
        return QRPolynomial(num, 0).mod(e)


class QRRSBlock:

    RS_BLOCK_TABLE = [

        # L
        # M
        # Q
        # H

        # 1
        [1, 26, 19],
        [1, 26, 16],
        [1, 26, 13],
        [1, 26, 9],

        # 2
        [1, 44, 34],
        [1, 44, 28],
        [1, 44, 22],
        [1, 44, 16],

        # 3
        [1, 70, 55],
        [1, 70, 44],
        [2, 35, 17],
        [2, 35, 13],

        # 4
        [1, 100, 80],
        [2, 50, 32],
        [2, 50, 24],
        [4, 25, 9],

        # 5
        [1, 134, 108],
        [2, 67, 43],
        [2, 33, 15, 2, 34, 16],
        [2, 33, 11, 2, 34, 12],

        # 6
        [2, 86, 68],
        [4, 43, 27],
        [4, 43, 19],
        [4, 43, 15],

        # 7
        [2, 98, 78],
        [4, 49, 31],
        [2, 32, 14, 4, 33, 15],
        [4, 39, 13, 1, 40, 14],

        # 8
        [2, 121, 97],
        [2, 60, 38, 2, 61, 39],
        [4, 40, 18, 2, 41, 19],
        [4, 40, 14, 2, 41, 15],

        # 9
        [2, 146, 116],
        [3, 58, 36, 2, 59, 37],
        [4, 36, 16, 4, 37, 17],
        [4, 36, 12, 4, 37, 13],

        # 10
        [2, 86, 68, 2, 87, 69],
        [4, 69, 43, 1, 70, 44],
        [6, 43, 19, 2, 44, 20],
        [6, 43, 15, 2, 44, 16],

        # 11
        [4, 101, 81],
        [1, 80, 50, 4, 81, 51],
        [4, 50, 22, 4, 51, 23],
        [3, 36, 12, 8, 37, 13],

        # 12
        [2, 116, 92, 2, 117, 93],
        [6, 58, 36, 2, 59, 37],
        [4, 46, 20, 6, 47, 21],
        [7, 42, 14, 4, 43, 15],

        # 13
        [4, 133, 107],
        [8, 59, 37, 1, 60, 38],
        [8, 44, 20, 4, 45, 21],
        [12, 33, 11, 4, 34, 12],

        # 14
        [3, 145, 115, 1, 146, 116],
        [4, 64, 40, 5, 65, 41],
        [11, 36, 16, 5, 37, 17],
        [11, 36, 12, 5, 37, 13],

        # 15
        [5, 109, 87, 1, 110, 88],
        [5, 65, 41, 5, 66, 42],
        [5, 54, 24, 7, 55, 25],
        [11, 36, 12],

        # 16
        [5, 122, 98, 1, 123, 99],
        [7, 73, 45, 3, 74, 46],
        [15, 43, 19, 2, 44, 20],
        [3, 45, 15, 13, 46, 16],

        # 17
        [1, 135, 107, 5, 136, 108],
        [10, 74, 46, 1, 75, 47],
        [1, 50, 22, 15, 51, 23],
        [2, 42, 14, 17, 43, 15],

        # 18
        [5, 150, 120, 1, 151, 121],
        [9, 69, 43, 4, 70, 44],
        [17, 50, 22, 1, 51, 23],
        [2, 42, 14, 19, 43, 15],

        # 19
        [3, 141, 113, 4, 142, 114],
        [3, 70, 44, 11, 71, 45],
        [17, 47, 21, 4, 48, 22],
        [9, 39, 13, 16, 40, 14],

        # 20
        [3, 135, 107, 5, 136, 108],
        [3, 67, 41, 13, 68, 42],
        [15, 54, 24, 5, 55, 25],
        [15, 43, 15, 10, 44, 16],

        # 21
        [4, 144, 116, 4, 145, 117],
        [17, 68, 42],
        [17, 50, 22, 6, 51, 23],
        [19, 46, 16, 6, 47, 17],

        # 22
        [2, 139, 111, 7, 140, 112],
        [17, 74, 46],
        [7, 54, 24, 16, 55, 25],
        [34, 37, 13],

        # 23
        [4, 151, 121, 5, 152, 122],
        [4, 75, 47, 14, 76, 48],
        [11, 54, 24, 14, 55, 25],
        [16, 45, 15, 14, 46, 16],

        # 24
        [6, 147, 117, 4, 148, 118],
        [6, 73, 45, 14, 74, 46],
        [11, 54, 24, 16, 55, 25],
        [30, 46, 16, 2, 47, 17],

        # 25
        [8, 132, 106, 4, 133, 107],
        [8, 75, 47, 13, 76, 48],
        [7, 54, 24, 22, 55, 25],
        [22, 45, 15, 13, 46, 16],

        # 26
        [10, 142, 114, 2, 143, 115],
        [19, 74, 46, 4, 75, 47],
        [28, 50, 22, 6, 51, 23],
        [33, 46, 16, 4, 47, 17],

        # 27
        [8, 152, 122, 4, 153, 123],
        [22, 73, 45, 3, 74, 46],
        [8, 53, 23, 26, 54, 24],
        [12, 45, 15, 28, 46, 16],

        # 28
        [3, 147, 117, 10, 148, 118],
        [3, 73, 45, 23, 74, 46],
        [4, 54, 24, 31, 55, 25],
        [11, 45, 15, 31, 46, 16],

        # 29
        [7, 146, 116, 7, 147, 117],
        [21, 73, 45, 7, 74, 46],
        [1, 53, 23, 37, 54, 24],
        [19, 45, 15, 26, 46, 16],

        # 30
        [5, 145, 115, 10, 146, 116],
        [19, 75, 47, 10, 76, 48],
        [15, 54, 24, 25, 55, 25],
        [23, 45, 15, 25, 46, 16],

        # 31
        [13, 145, 115, 3, 146, 116],
        [2, 74, 46, 29, 75, 47],
        [42, 54, 24, 1, 55, 25],
        [23, 45, 15, 28, 46, 16],

        # 32
        [17, 145, 115],
        [10, 74, 46, 23, 75, 47],
        [10, 54, 24, 35, 55, 25],
        [19, 45, 15, 35, 46, 16],

        # 33
        [17, 145, 115, 1, 146, 116],
        [14, 74, 46, 21, 75, 47],
        [29, 54, 24, 19, 55, 25],
        [11, 45, 15, 46, 46, 16],

        # 34
        [13, 145, 115, 6, 146, 116],
        [14, 74, 46, 23, 75, 47],
        [44, 54, 24, 7, 55, 25],
        [59, 46, 16, 1, 47, 17],

        # 35
        [12, 151, 121, 7, 152, 122],
        [12, 75, 47, 26, 76, 48],
        [39, 54, 24, 14, 55, 25],
        [22, 45, 15, 41, 46, 16],

        # 36
        [6, 151, 121, 14, 152, 122],
        [6, 75, 47, 34, 76, 48],
        [46, 54, 24, 10, 55, 25],
        [2, 45, 15, 64, 46, 16],

        # 37
        [17, 152, 122, 4, 153, 123],
        [29, 74, 46, 14, 75, 47],
        [49, 54, 24, 10, 55, 25],
        [24, 45, 15, 46, 46, 16],

        # 38
        [4, 152, 122, 18, 153, 123],
        [13, 74, 46, 32, 75, 47],
        [48, 54, 24, 14, 55, 25],
        [42, 45, 15, 32, 46, 16],

        # 39
        [20, 147, 117, 4, 148, 118],
        [40, 75, 47, 7, 76, 48],
        [43, 54, 24, 22, 55, 25],
        [10, 45, 15, 67, 46, 16],

        # 40
        [19, 148, 118, 6, 149, 119],
        [18, 75, 47, 31, 76, 48],
        [34, 54, 24, 34, 55, 25],
        [20, 45, 15, 61, 46, 16]

    ]

    def __init__(self, totalCount, dataCount):
        self.totalCount = totalCount
        self.dataCount = dataCount

    @staticmethod
    def getRSBlocks(typeNumber, errorCorrectLevel):
        rs_block = QRRSBlock.getRsBlockTable(typeNumber, errorCorrectLevel)
        if rs_block == None:
            raise Exception("bad rs block @ typeNumber:" + typeNumber +
                "/errorCorrectLevel:" + errorCorrectLevel)

        length = len(rs_block) / 3

        blocks = []

        for i in range(length):

            count = rs_block[i * 3 + 0]
            totalCount = rs_block[i * 3 + 1]
            dataCount = rs_block[i * 3 + 2]

            for j in range(count):
                blocks.append(QRRSBlock(totalCount, dataCount))

        return blocks

    @staticmethod
    def getRsBlockTable(typeNumber, errorCorrectLevel):
        if errorCorrectLevel == constants.ERROR_CORRECT_L:
            return QRRSBlock.RS_BLOCK_TABLE[(typeNumber - 1) * 4 + 0]
        elif errorCorrectLevel == constants.ERROR_CORRECT_M:
            return QRRSBlock.RS_BLOCK_TABLE[(typeNumber - 1) * 4 + 1]
        elif errorCorrectLevel == constants.ERROR_CORRECT_Q:
            return QRRSBlock.RS_BLOCK_TABLE[(typeNumber - 1) * 4 + 2]
        elif errorCorrectLevel == constants.ERROR_CORRECT_H:
            return QRRSBlock.RS_BLOCK_TABLE[(typeNumber - 1) * 4 + 3]


class QRBitBuffer:
    def __init__(self):
        self.buffer = []
        self.length = 0

    def __repr__(self):
        return ".".join([str(n) for n in self.buffer])

    def get(self, index):
        bufIndex = math.floor(index / 8)
        return ((self.buffer[bufIndex] >> (7 - index % 8)) & 1) == 1

    def put(self, num, length):
        for i in range(length):
            self.putBit(((num >> (length - i - 1)) & 1) == 1)

    def getLengthInBits(self):
        return self.length

    def putBit(self, bit):
        bufIndex = self.length // 8
        if len(self.buffer) <= bufIndex:
            self.buffer.append(0)
        if bit:
            self.buffer[bufIndex] |= (0x80 >> (self.length % 8))
        self.length += 1
