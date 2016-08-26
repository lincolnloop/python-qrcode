class BitBuffer:
    def __init__(self, data=None, colors=None):
        self.buffer = []
        self.colors = []
        color_index = 0
        if None == data:
            return
        for b in data:
            if None == colors:
                self.put_byte(b)
            else:
                if not isinstance(b, int):
                    b = ord(b)
                for bit_index in xrange(8):
                    self.put_bit(self.get_bit_from_num(b, bit_index), colors[color_index])
                    color_index += 1

    def __repr__(self):
        return ".".join([str(n) for n in self.buffer])

    def __len__(self):
        return len(self.colors)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.get_bit(index)
        if None != index.step:
            raise RuntimeError("Stop slice of BitBuffer not supported")
        result = BitBuffer()
        if None == index.stop:
            stop = len(self)
        else:
            stop = index.stop
        if None == index.start:
            start = 0
        else:
            start = index.start
        for index in xrange(start, stop):
            result.put_bit_with_color(self.get_bit(index))
        return result

    def __add__(self, other):
        for index in xrange(len(other)):
            self.put_bit_with_color(other.get_bit(index))
        return self

    def get_bit_from_num(self, b_int, bit_index, bits_in_num=8):
        return ((b_int >> (bits_in_num - 1 - bit_index)) & 1) == 1

    def make_bytes(self):
        return bytearray(self.buffer)

    def put(self, num, length, color):
        for i in range(length):
            self.put_bit(self.get_bit_from_num(num, i, length), color)

    def put_byte(self, b, color):
        if not isinstance(b, int):
            b = ord(b)
        self.put(b, 8, color)

    def put_bit(self, bit, color):
        buf_index = len(self) // 8
        if len(self.buffer) <= buf_index:
            self.buffer.append(0)
        if bit:
            self.buffer[buf_index] |= (0x80 >> (len(self) % 8))
        self.colors.append(color)

    def put_bit_with_color(self, bit_with_color):
        self.put_bit(bit_with_color[0], bit_with_color[1])

    def get_bit(self, index):
        buf_index = index // 8
        return (((self.buffer[buf_index] >> (7 - index % 8)) & 1) == 1, self.colors[index])

    def set_color(self, index, color):
        self.colors[index] = color

    def get_color(self, index):
        return self.colors[index]