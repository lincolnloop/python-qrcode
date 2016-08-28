class BitBuffer:
    def __init__(self, data=None):
        self.buffer = []
        self.length = 0
        if None != data:
            for b in data:
                self.put_byte(b)

    def __repr__(self):
        return ".".join([str(n) for n in self.buffer])

    def __len__(self):
        return self.length

    def __getitem__(self, index):
        return BitBuffer(self.buffer.__getitem__(index))

    def __add__(self, other):
        for index in xrange(len(other)):
            self.put_bit(other.get_bit(index))

    def make_bytes(self):
        return bytearray(self.buffer)

    def put(self, num, length):
        for i in range(length):
            self.put_bit(((num >> (length - i - 1)) & 1) == 1)

    def put_byte(self, b):
        self.put(ord(b), 8)

    def put_bit(self, bit):
        buf_index = self.length // 8
        if len(self.buffer) <= buf_index:
            self.buffer.append(0)
        if bit:
            self.buffer[buf_index] |= (0x80 >> (self.length % 8))
        self.length += 1

    def get_bit(self, index):
        buf_index = index // 8
        return ((self.buffer[buf_index] >> (7 - index % 8)) & 1) == 1


