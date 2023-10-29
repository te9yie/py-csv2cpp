import array
import copy
import struct


class Binary:
    def __init__(self):
        self.bin = array.array("B")

    def append(self, format, *value):
        self.bin.extend(self.make_binary(format, *value))

    def append_string(self, text: str):
        text_length = len(text) + 1
        self.append("%ds" % text_length, text)

    def __len__(self) -> int:
        return len(self.bin)

    def __iadd__(self, other):
        self.bin.extend(other.bin)
        return self

    def __add__(self, other):
        bin = copy.deepcopy(self)
        bin += other
        return bin

    def make_binary(self, format, *value):
        return array.array("B", struct.pack(format, *value))

    def align(self, size):
        remain = len(self.bin) % size
        if remain != 0:
            padding_size = size - remain
            self.append("B" * padding_size, *[0] * padding_size)

    def tofile(self, path):
        self.bin.tofile(path)
