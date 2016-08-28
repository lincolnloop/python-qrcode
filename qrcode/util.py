import re
import bisect
import reedsolo
from StringIO import StringIO
from itertools import izip_longest

import six
from six.moves import xrange

from collections import defaultdict
from qrcode import base, exceptions

from .bitbuffer import BitBuffer

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

BITS_FOR_MODE = 4

NUMERIC_ONLY = six.b('0123456789')
ALPHA_NUM = six.b('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:')
BINARY_BYTE = six.b(''.join([chr(x) for x in range(0x100)]))
RE_ALPHA_NUM = re.compile(six.b('^[') + re.escape(ALPHA_NUM) + six.b(']*\Z'))

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

G15 = (
    (1 << 10) | (1 << 8) | (1 << 5) | (1 << 4) | (1 << 2) | (1 << 1) |
    (1 << 0))
G18 = (
    (1 << 12) | (1 << 11) | (1 << 10) | (1 << 9) | (1 << 8) | (1 << 5) |
    (1 << 2) | (1 << 0))
G15_MASK = (1 << 14) | (1 << 12) | (1 << 10) | (1 << 4) | (1 << 1)

PAD0 = 0xEC
PAD1 = 0x11

MAX_VERSION = 40

# Precompute bit count limits, indexed by error correction level and code size
_data_count = lambda block: block.data_count
BIT_LIMIT_TABLE = [
    [0] + [8*sum(map(_data_count, base.rs_blocks(version, error_correction)))
           for version in xrange(1, MAX_VERSION+1)]
    for error_correction in xrange(4)
]


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
        return lambda i, j: ((i // 2) + (j // 3)) % 2 == 0
    if pattern == 5:  # 101
        return lambda i, j: (i * j) % 2 + (i * j) % 3 == 0
    if pattern == 6:  # 110
        return lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0
    if pattern == 7:  # 111
        return lambda i, j: ((i * j) % 3 + (i + j) % 2) % 2 == 0
    raise TypeError("Bad mask pattern: " + pattern)  # pragma: no cover


def mode_sizes_for_version(version):
    if version < 10:
        return MODE_SIZE_SMALL
    elif version < 27:
        return MODE_SIZE_MEDIUM
    else:
        return MODE_SIZE_LARGE


def length_in_bits(mode, version):
    if mode not in (
            MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE, MODE_KANJI):
        raise TypeError("Invalid mode (%s)" % mode)  # pragma: no cover

    if version < 1 or version > 40:  # pragma: no cover
        raise ValueError(
            "Invalid version (was %s, expected 1 to 40)" % version)

    return mode_sizes_for_version(version)[mode]


def lost_point(modules):
    modules_count = len(modules)

    lost_point = 0

    lost_point = _lost_point_level1(modules, modules_count)
    lost_point += _lost_point_level2(modules, modules_count)
    lost_point += _lost_point_level3(modules, modules_count)
    lost_point += _lost_point_level4(modules, modules_count)

    return lost_point


def _lost_point_level1(modules, modules_count):
    lost_point = 0

    modules_range = xrange(modules_count)
    row_range_first = (0, 1)
    row_range_last = (-1, 0)
    row_range_standard = (-1, 0, 1)

    col_range_first = ((0, 1), (1,))
    col_range_last = ((-1, 0), (-1,))
    col_range_standard = ((-1, 0, 1), (-1, 1))

    for row in modules_range:

        if row == 0:
            row_range = row_range_first
        elif row == modules_count-1:
            row_range = row_range_last
        else:
            row_range = row_range_standard

        for col in modules_range:

            sameCount = 0
            dark = modules[row][col]

            if col == 0:
                col_range = col_range_first
            elif col == modules_count-1:
                col_range = col_range_last
            else:
                col_range = col_range_standard

            for r in row_range:

                row_offset = row + r

                if r != 0:
                    col_idx = 0
                else:
                    col_idx = 1

                for c in col_range[col_idx]:

                    if dark == modules[row_offset][col + c]:
                        sameCount += 1

            if sameCount > 5:
                lost_point += (3 + sameCount - 5)

    return lost_point


def _lost_point_level2(modules, modules_count):
    lost_point = 0

    modules_range = xrange(modules_count - 1)

    for row in modules_range:
        this_row = modules[row]
        next_row = modules[row+1]
        for col in modules_range:
            count = 0
            if this_row[col]:
                count += 1
            if next_row[col]:
                count += 1
            if this_row[col + 1]:
                count += 1
            if next_row[col + 1]:
                count += 1
            if count == 0 or count == 4:
                lost_point += 3

    return lost_point


def _lost_point_level3(modules, modules_count):
    modules_range_short = xrange(modules_count-6)

    lost_point = 0
    for row in xrange(modules_count):
        this_row = modules[row]
        for col in modules_range_short:
            if (this_row[col]
                    and not this_row[col + 1]
                    and this_row[col + 2]
                    and this_row[col + 3]
                    and this_row[col + 4]
                    and not this_row[col + 5]
                    and this_row[col + 6]):
                lost_point += 40

    for col in xrange(modules_count):
        for row in modules_range_short:
            if (modules[row][col]
                    and not modules[row + 1][col]
                    and modules[row + 2][col]
                    and modules[row + 3][col]
                    and modules[row + 4][col]
                    and not modules[row + 5][col]
                    and modules[row + 6][col]):
                lost_point += 40

    return lost_point


def _lost_point_level4(modules, modules_count):
    modules_range = xrange(modules_count)
    dark_count = 0

    for row in modules_range:
        this_row = modules[row]
        for col in modules_range:
            if this_row[col]:
                dark_count += 1

    ratio = abs(100 * dark_count / modules_count / modules_count - 50) / 5
    return ratio * 10


def optimal_data_chunks(data, minimum=4, error_correction=0):
    """
    An iterator returning QRData chunks optimized to the data content.

    :param minimum: The minimum number of bytes in a row to split as a chunk.
    """
    data = to_bytestring(data)
    for version in xrange(1, MAX_VERSION + 1):
        data_list = encode_with_version(data, version)
        if None != data_list and len(data_list) <= BIT_LIMIT_TABLE[error_correction][version]:
            break
        else:
            data_list = None
    if None == data_list:
        raise exceptions.DataOverflowError()

    data_chunks = []
    last_mode = data_list[0][1]
    chunk = ''
    for data, mode in data_list:
        if last_mode != mode:
            data_chunks.append(QRData(chunk, last_mode))
            chunk = data
            last_mode = mode
        else:
            chunk += data
    data_chunks.append(QRData(chunk, last_mode))
    return data_chunks

def _optimal_split(data, pattern):
    while data:
        match = re.search(pattern, data)
        if not match:
            break
        start, end = match.start(), match.end()
        if start:
            yield False, data[:start]
        yield True, data[start:end]
        data = data[end:]
    if data:
        yield False, data


def to_bytestring(data):
    """
    Convert data to a (utf-8 encoded) byte-string if it isn't a byte-string
    already.
    """
    if not isinstance(data, six.binary_type):
        data = six.text_type(data).encode('utf-8')
    return data


def optimal_mode(data):
    """
    Calculate the optimal mode for this chunk of data.
    """
    if data.isdigit():
        return MODE_NUMBER
    if RE_ALPHA_NUM.match(data):
        return MODE_ALPHA_NUM
    return MODE_8BIT_BYTE


class QRData:
    """
    Data held in a QR compatible format.

    Doesn't currently handle KANJI.
    """

    def __init__(self, data, mode=None, check_data=True):
        """
        If ``mode`` isn't provided, the most compact QR data type possible is
        chosen.
        """
        if check_data:
            data = to_bytestring(data)

        if mode is None:
            self.mode = optimal_mode(data)
        else:
            self.mode = mode
            if mode not in (MODE_NUMBER, MODE_ALPHA_NUM, MODE_8BIT_BYTE):
                raise TypeError("Invalid mode (%s)" % mode)  # pragma: no cover
            if check_data and mode < optimal_mode(data):  # pragma: no cover
                raise ValueError(
                    "Provided data can not be represented in mode "
                    "{0}".format(mode))

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
                    buffer.put(
                        ALPHA_NUM.find(chars[0]) * 45 +
                        ALPHA_NUM.find(chars[1]), 11)
                else:
                    buffer.put(ALPHA_NUM.find(chars), 6)
        else:
            if six.PY3:
                # Iterating a bytestring in Python 3 returns an integer,
                # no need to ord().
                data = self.data
            else:
                data = [ord(c) for c in self.data]
            for c in data:
                buffer.put(c, 8)

    def __repr__(self):
        return repr(self.data)

def create_data(version, error_correction, data_list):

    buffer = BitBuffer()
    for data in data_list:
        buffer.put(data.mode, 4)
        buffer.put(len(data), length_in_bits(data.mode, version))
        data.write(buffer)

    # Calculate the maximum number of bits for the given version.
    rs_blocks = base.rs_blocks(version, error_correction)
    bit_limit = 0
    for block in rs_blocks:
        bit_limit += block.data_count * 8

    if len(buffer) > bit_limit:
        raise exceptions.DataOverflowError(
            "Code length overflow. Data size (%s) > size available (%s)" %
            (len(buffer), bit_limit))

    # Terminate the bits (add up to four 0s).
    for i in range(min(bit_limit - len(buffer), 4)):
        buffer.put_bit(False)

    # Delimit the string into 8-bit words, padding with 0s if necessary.
    delimit = len(buffer) % 8
    if delimit:
        buffer.put(0, 8 - delimit)

    # Add special alternating padding bitstrings until buffer is full.
    bytes_to_fill = (bit_limit - len(buffer)) // 8
    for i in range(bytes_to_fill):
        if i % 2 == 0:
            buffer.put(PAD0, 8)
        else:
            buffer.put(PAD1, 8)

    data_and_error_correction = generate_error_correction(buffer, rs_blocks)
    encoded_data = combain_data_and_error_correction(data_and_error_correction)
    return encoded_data

def generate_error_correction(buffer, rs_blocks):
    data = StringIO(bytearray(buffer.buffer))
    result = []
    for rs_block in rs_blocks:
        chunk = data.read(rs_block.data_count)
        if len(chunk) != rs_block.data_count:
            raise Exception("Out of data")
        num_of_ec_bytes = rs_block.total_count - rs_block.data_count
        result.append((bytearray(chunk), reedsolo.RSCodec(num_of_ec_bytes).encode(bytearray(chunk))[-num_of_ec_bytes:]))
    return result

def combain_data_and_error_correction(data_and_error_correction):
    result = []

    data_bytes = [x[0] for x in data_and_error_correction]
    ec_bytes = [x[1] for x in data_and_error_correction]
    for data in [data_bytes, ec_bytes]:
        for chunk in izip_longest(*data):
            for c in list(chunk):
                if None != c:
                    result.append(c)

    return result

def add_edge(graph, source, char_index, char, mode_sizes):
    targets = set()
    if char in NUMERIC_ONLY:
        bits_for_char = 4
        combined = 0
        if source.startswith('NUM_'):
            bits_for_mode = 0
            if source.endswith('_0'):
                bits_for_char = 3
                combined = 1
            elif source.endswith('_1'):
                bits_for_char = 3
                combined = 2
        else:
            bits_for_mode = BITS_FOR_MODE + mode_sizes[MODE_NUMBER]
        target = 'NUM_%04d_%s_%d' % (char_index, char, combined)
        graph[source][target] = bits_for_mode + bits_for_char
        targets.add(target)
    if char in ALPHA_NUM:
        bits_for_char = 6
        combined = 0
        if source.startswith('ALP_'):
            bits_for_mode = 0
            if source.endswith('_0'):
                bits_for_char = 5
                combined = 1
        else:
            bits_for_mode = BITS_FOR_MODE + mode_sizes[MODE_ALPHA_NUM]
        target = 'ALP_%04d_%s_%d' % (char_index, char, combined)
        graph[source][target] = bits_for_mode + bits_for_char
        targets.add(target)
    if char in BINARY_BYTE:
        if source.startswith('BIN_'):
            bits_for_mode = 0
        else:
            bits_for_mode = BITS_FOR_MODE + mode_sizes[MODE_8BIT_BYTE]
        target = 'BIN_%04d_%s' % (char_index, char)
        graph[source][target] = bits_for_mode + 8
        targets.add(target)
    if source.startswith('KAN_'):
        bits_for_mode = 0
    else:
        bits_for_mode = BITS_FOR_MODE + mode_sizes[MODE_KANJI]
    target = 'KAN_%04d_%s' % (char_index, char)
    graph[source][target] = bits_for_mode + 13
    targets.add(target)
    return targets

def make_flow_graph_from_data(data, mode_sizes):
    graph = defaultdict(dict)
    if 0 == len(data):
        return graph
    sources = add_edge(graph, 'start', 0, data[0], mode_sizes)
    for i in xrange(1, len(data)):
        targets = set()
        for src in sources:
            targets.update(add_edge(graph, src, i, data[i], mode_sizes))
        sources = targets
    for src in sources:
        graph[src]['end'] = 0
    return graph

# http://code.activestate.com/recipes/117228/
# Priority dictionary using binary heaps
# David Eppstein, UC Irvine, 8 Mar 2002
class priorityDictionary(dict):
    def __init__(self):
        '''Initialize priorityDictionary by creating binary heap
of pairs (value,key).  Note that changing or removing a dict entry will
not remove the old pair from the heap until it is found by smallest() or
until the heap is rebuilt.'''
        self.__heap = []
        dict.__init__(self)

    def smallest(self):
        '''Find smallest item after removing deleted items from heap.'''
        if len(self) == 0:
            raise IndexError, "smallest of empty priorityDictionary"
        heap = self.__heap
        while heap[0][1] not in self or self[heap[0][1]] != heap[0][0]:
            lastItem = heap.pop()
            insertionPoint = 0
            while 1:
                smallChild = 2*insertionPoint+1
                if smallChild+1 < len(heap) and \
                        heap[smallChild] > heap[smallChild+1]:
                    smallChild += 1
                if smallChild >= len(heap) or lastItem <= heap[smallChild]:
                    heap[insertionPoint] = lastItem
                    break
                heap[insertionPoint] = heap[smallChild]
                insertionPoint = smallChild
        return heap[0][1]

    def __iter__(self):
        '''Create destructive sorted iterator of priorityDictionary.'''
        def iterfn():
            while len(self) > 0:
                x = self.smallest()
                yield x
                del self[x]
        return iterfn()

    def __setitem__(self,key,val):
        '''Change value stored in dictionary and add corresponding
pair to heap.  Rebuilds the heap if the number of deleted items grows
too large, to avoid memory leakage.'''
        dict.__setitem__(self,key,val)
        heap = self.__heap
        if len(heap) > 2 * len(self):
            self.__heap = [(v,k) for k,v in self.iteritems()]
            self.__heap.sort()  # builtin sort likely faster than O(n) heapify
        else:
            newPair = (val,key)
            insertionPoint = len(heap)
            heap.append(None)
            while insertionPoint > 0 and \
                    newPair < heap[(insertionPoint-1)//2]:
                heap[insertionPoint] = heap[(insertionPoint-1)//2]
                insertionPoint = (insertionPoint-1)//2
            heap[insertionPoint] = newPair

    def setdefault(self,key,val):
        '''Reimplement setdefault to call our customized __setitem__.'''
        if key not in self:
            self[key] = val
        return self[key]

# Dijkstra's algorithm for shortest paths
# David Eppstein, UC Irvine, 4 April 2002
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/117228
def Dijkstra(G, start, end=None):
    """
    Find shortest paths from the start vertex to all
    vertices nearer than or equal to the end.

    The input graph G is assumed to have the following
    representation: A vertex can be any object that can
    be used as an index into a dictionary.  G is a
    dictionary, indexed by vertices.  For any vertex v,
    G[v] is itself a dictionary, indexed by the neighbors
    of v.  For any edge v->w, G[v][w] is the length of
    the edge.  This is related to the representation in
    <http://www.python.org/doc/essays/graphs.html>
    where Guido van Rossum suggests representing graphs
    as dictionaries mapping vertices to lists of neighbors,
    however dictionaries of edges have many advantages
    over lists: they can store extra information (here,
    the lengths), they support fast existence tests,
    and they allow easy modification of the graph by edge
    insertion and removal.  Such modifications are not
    needed here but are important in other graph algorithms.
    Since dictionaries obey iterator protocol, a graph
    represented as described here could be handed without
    modification to an algorithm using Guido's representation.

    Of course, G and G[v] need not be Python dict objects;
    they can be any other object that obeys dict protocol,
    for instance a wrapper in which vertices are URLs
    and a call to G[v] loads the web page and finds its links.

    The output is a pair (D,P) where D[v] is the distance
    from start to v and P[v] is the predecessor of v along
    the shortest path from s to v.

    Dijkstra's algorithm is only guaranteed to work correctly
    when all edge lengths are positive. This code does not
    verify this property for all edges (only the edges seen
    before the end vertex is reached), but will correctly
    compute shortest paths even for some graphs with negative
    edges, and will raise an exception if it discovers that
    a negative edge has caused it to make a mistake.
    """

    D = {}  # dictionary of final distances
    P = {}  # dictionary of predecessors
    Q = priorityDictionary()   # est.dist. of non-final vert.
    Q[start] = 0

    for v in Q:
        D[v] = Q[v]
        if v == end: break

        for w in G[v]:
            vwLength = D[v] + G[v][w]
            if w in D:
                if vwLength < D[w]:
                    raise ValueError, \
  "Dijkstra: found better path to already-final vertex"
            elif w not in Q or vwLength < Q[w]:
                Q[w] = vwLength
                P[w] = v

    return (D,P)

def shortestPath(G, start, end):
    """
    Find a single shortest path from the given start vertex
    to the given end vertex.
    The input has the same conventions as Dijkstra().
    The output is a list of the vertices in order along
    the shortest path.
    """

    D,P = Dijkstra(G,start,end)
    Path = []
    while 1:
        Path.append(end)
        if end == start: break
        end = P[end]
    Path.reverse()
    return Path

def mode_name_to_mode(name):
    if name == 'BIN':
        return MODE_8BIT_BYTE
    elif name == 'NUM':
        return MODE_NUMBER
    elif name == 'ALP':
        return MODE_ALPHA_NUM
    elif name == 'KAN':
        return MODE_KANJI
    else:
        raise ValueError, "Invalid mode %r" % name

def encode_with_version(data, version):
    mode_sizes = mode_sizes_for_version(version)
    flow_graph = make_flow_graph_from_data(data, mode_sizes)
    shortest_path = shortestPath(flow_graph, 'start', 'end')
    return [(c, mode_name_to_mode(enc[:3])) for c, enc in zip(data, shortest_path[1:-1])]
