from __future__ import annotations
import array
import copy
import struct
from typing import IO, Any


class Binary:
    def __init__(self):
        self.bin = array.array("B")

    def append(self, format: str, *value: Any):
        self.bin.extend(self.make_binary(format, *value))

    def append_string(self, text: str):
        text_length = len(text) + 1
        self.append("%ds" % text_length, text.encode())

    def __len__(self) -> int:
        return len(self.bin)

    def __iadd__(self, other: Binary):
        self.bin.extend(other.bin)
        return self

    def __add__(self, other: Binary):
        bin = copy.deepcopy(self)
        bin += other
        return bin

    def make_binary(self, format: str, *value: Any):
        return array.array("B", struct.pack(format, *value))

    def align(self, size: int):
        remain = len(self.bin) % size
        if remain != 0:
            padding_size = size - remain
            self.append("B" * padding_size, *[0] * padding_size)

    def tofile(self, path: IO):
        self.bin.tofile(path)


if __name__ == "__main__":
    import unittest

    class TestBinary(unittest.TestCase):
        def test_append_string(self):
            bin = Binary()
            bin.append_string("HELLO")
            self.assertEqual(len(bin), 6)

    unittest.main()
