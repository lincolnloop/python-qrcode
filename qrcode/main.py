from PIL import Image, ImageDraw

from qrcode.base import QR8bitByte, QRUtil, QRRSBlock, QRBitBuffer, \
    QRPolynomial
from qrcode import constants


class DataOverflowError(Exception):
    pass


class QRCode:

    def __init__(self, qr_type=None,
            error_correct_level=constants.ERROR_CORRECT_M, box_size=10):
        self.typeNumber = qr_type
        self.errorCorrectLevel = error_correct_level
        self.modules = None
        self.moduleCount = 0
        self.dataCache = None
        self.dataList = []
        self.box_size = box_size

    def addData(self, data):
        newData = QR8bitByte(data)
        self.dataList.append(newData)
        self.dataCache = None

    def make(self, fit=True):
        if fit:
            self.best_fit(start=self.typeNumber)
        self.makeImpl(False, self.getBestMaskPattern())

    def makeImpl(self, test, maskPattern):
        self.moduleCount = self.typeNumber * 4 + 17
        self.modules = [None for x in range(self.moduleCount)]

        for row in range(self.moduleCount):

            self.modules[row] = [None for x in range(self.moduleCount)]

            for col in range(self.moduleCount):
                self.modules[row][col] = None   # (col + row) % 3

        self.setupPositionProbePattern(0, 0)
        self.setupPositionProbePattern(self.moduleCount - 7, 0)
        self.setupPositionProbePattern(0, self.moduleCount - 7)
        self.setupPositionAdjustPattern()
        self.setupTimingPattern()
        self.setupTypeInfo(test, maskPattern)

        if (self.typeNumber >= 7):
            self.setupTypeNumber(test)

        if (self.dataCache == None):
            self.dataCache = QRCode.createData(self.typeNumber,
                self.errorCorrectLevel, self.dataList)
        self.mapData(self.dataCache, maskPattern)

    def setupPositionProbePattern(self, row, col):
        for r in range(-1, 8):

            if (row + r <= -1 or self.moduleCount <= row + r):
                continue

            for c in range(-1, 8):

                if (col + c <= -1 or self.moduleCount <= col + c):
                    continue

                if ((0 <= r and r <= 6 and (c == 0 or c == 6))
                        or (0 <= c and c <= 6 and (r == 0 or r == 6))
                        or (2 <= r and r <= 4 and 2 <= c and c <= 4)):
                    self.modules[row + r][col + c] = True
                else:
                    self.modules[row + r][col + c] = False

    def best_fit(self, start=None):
        """
        Set ``typeNumber`` the minimum size required to fit in the data.
        """
        size = start or 1
        while True:
            try:
                self.dataCache = QRCode.createData(size,
                    self.errorCorrectLevel, self.dataList)
            except DataOverflowError:
                size += 1
            else:
                self.typeNumber = size
                return size

    def getBestMaskPattern(self):
        minLostPoint = 0
        pattern = 0

        for i in range(8):

            self.makeImpl(True, i)

            lostPoint = QRUtil.getLostPoint(self)

            if (i == 0 or minLostPoint > lostPoint):
                minLostPoint = lostPoint
                pattern = i

        return pattern

    def makeImage(self):
        offset = 4   # Spec says border should be at least four boxes wide
        pixelsize = (self.moduleCount + offset * 2) * self.box_size

        im = Image.new("1", (pixelsize, pixelsize), "white")
        d = ImageDraw.Draw(im)

        for r in range(self.moduleCount):
            for c in range(self.moduleCount):
                if (self.modules[r][c]):
                    x = (c + offset) * self.box_size
                    y = (r + offset) * self.box_size
                    b = [(x, y),
                        (x + self.box_size - 1, y + self.box_size - 1)]
                    d.rectangle(b, fill="black")
        return im

    def setupTimingPattern(self):
        for r in range(8, self.moduleCount - 8):
            if (self.modules[r][6] != None):
                continue
            self.modules[r][6] = (r % 2 == 0)

        for c in range(8, self.moduleCount - 8):
            if (self.modules[6][c] != None):
                continue
            self.modules[6][c] = (c % 2 == 0)

    def setupPositionAdjustPattern(self):
        pos = QRUtil.getPatternPosition(self.typeNumber)

        for i in range(len(pos)):

            for j in range(len(pos)):

                row = pos[i]
                col = pos[j]

                if (self.modules[row][col] != None):
                    continue

                for r in range(-2, 3):

                    for c in range(-2, 3):

                        if (r == -2 or r == 2 or c == -2 or c == 2 or
                                (r == 0 and c == 0)):
                            self.modules[row + r][col + c] = True
                        else:
                            self.modules[row + r][col + c] = False

    def setupTypeNumber(self, test):
        bits = QRUtil.getBCHTypeNumber(self.typeNumber)

        for i in range(18):
            mod = (not test and ((bits >> i) & 1) == 1)
            self.modules[i // 3][i % 3 + self.moduleCount - 8 - 3] = mod

        for i in range(18):
            mod = (not test and ((bits >> i) & 1) == 1)
            self.modules[i % 3 + self.moduleCount - 8 - 3][i // 3] = mod

    def setupTypeInfo(self, test, maskPattern):
        data = (self.errorCorrectLevel << 3) | maskPattern
        bits = QRUtil.getBCHTypeInfo(data)

        # vertical
        for i in range(15):

            mod = (not test and ((bits >> i) & 1) == 1)

            if (i < 6):
                self.modules[i][8] = mod
            elif (i < 8):
                self.modules[i + 1][8] = mod
            else:
                self.modules[self.moduleCount - 15 + i][8] = mod

        # horizontal
        for i in range(15):

            mod = (not test and ((bits >> i) & 1) == 1)

            if (i < 8):
                self.modules[8][self.moduleCount - i - 1] = mod
            elif (i < 9):
                self.modules[8][15 - i - 1 + 1] = mod
            else:
                self.modules[8][15 - i - 1] = mod

        # fixed module
        self.modules[self.moduleCount - 8][8] = (not test)

    def mapData(self, data, maskPattern):
        inc = -1
        row = self.moduleCount - 1
        bitIndex = 7
        byteIndex = 0

        for col in range(self.moduleCount - 1, 0, -2):

            if (col == 6):
                col -= 1

            while (True):

                for c in range(2):

                    if (self.modules[row][col - c] == None):

                        dark = False

                        if (byteIndex < len(data)):
                            dark = (((data[byteIndex] >> bitIndex) & 1) == 1)

                        mask = QRUtil.getMask(maskPattern, row, col - c)

                        if (mask):
                            dark = not dark

                        self.modules[row][col - c] = dark
                        bitIndex -= 1

                        if (bitIndex == -1):
                            byteIndex += 1
                            bitIndex = 7

                row += inc

                if (row < 0 or self.moduleCount <= row):
                    row -= inc
                    inc = -inc
                    break

    PAD0 = 0xEC
    PAD1 = 0x11

    @staticmethod
    def createData(typeNumber, errorCorrectLevel, dataList):

        rsBlocks = QRRSBlock.getRSBlocks(typeNumber, errorCorrectLevel)

        buffer = QRBitBuffer()

        for i in range(len(dataList)):
            data = dataList[i]
            buffer.put(data.mode, 4)
            buffer.put(data.getLength(),
                QRUtil.getLengthInBits(data.mode, typeNumber))
            data.write(buffer)

        # calc num max data.
        totalDataCount = 0
        for i in range(len(rsBlocks)):
            totalDataCount += rsBlocks[i].dataCount

        if (buffer.getLengthInBits() > totalDataCount * 8):
            raise DataOverflowError("Code length overflow. Data size (%s) > "
                "size available (%s)" % (buffer.getLengthInBits(),
                    totalDataCount * 8))

        # end code
        if (buffer.getLengthInBits() + 4 <= totalDataCount * 8):
            buffer.put(0, 4)

        # padding
        while (buffer.getLengthInBits() % 8 != 0):
            buffer.putBit(False)

        # padding
        while True:

            if (buffer.getLengthInBits() >= totalDataCount * 8):
                break
            buffer.put(QRCode.PAD0, 8)

            if (buffer.getLengthInBits() >= totalDataCount * 8):
                break
            buffer.put(QRCode.PAD1, 8)

        return QRCode.createBytes(buffer, rsBlocks)

    @staticmethod
    def createBytes(buffer, rsBlocks):
        offset = 0

        maxDcCount = 0
        maxEcCount = 0

        dcdata = [0 for x in range(len(rsBlocks))]
        ecdata = [0 for x in range(len(rsBlocks))]

        for r in range(len(rsBlocks)):

            dcCount = rsBlocks[r].dataCount
            ecCount = rsBlocks[r].totalCount - dcCount

            maxDcCount = max(maxDcCount, dcCount)
            maxEcCount = max(maxEcCount, ecCount)

            dcdata[r] = [0 for x in range(dcCount)]

            for i in range(len(dcdata[r])):
                dcdata[r][i] = 0xff & buffer.buffer[i + offset]
            offset += dcCount

            rsPoly = QRUtil.getErrorCorrectPolynomial(ecCount)
            rawPoly = QRPolynomial(dcdata[r], rsPoly.getLength() - 1)

            modPoly = rawPoly.mod(rsPoly)
            ecdata[r] = [0 for x in range(rsPoly.getLength() - 1)]
            for i in range(len(ecdata[r])):
                modIndex = i + modPoly.getLength() - len(ecdata[r])
                if (modIndex >= 0):
                    ecdata[r][i] = modPoly.get(modIndex)
                else:
                    ecdata[r][i] = 0

        totalCodeCount = 0
        for i in range(len(rsBlocks)):
            totalCodeCount += rsBlocks[i].totalCount

        data = [None for x in range(totalCodeCount)]
        index = 0

        for i in range(maxDcCount):
            for r in range(len(rsBlocks)):
                if (i < len(dcdata[r])):
                    data[index] = dcdata[r][i]
                    index += 1

        for i in range(maxEcCount):
            for r in range(len(rsBlocks)):
                if (i < len(ecdata[r])):
                    data[index] = ecdata[r][i]
                    index += 1

        return data
