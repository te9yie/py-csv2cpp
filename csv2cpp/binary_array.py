import binary


class BinaryArray:
    class Item:
        def __init__(self, id, bin):
            self.id = id
            self.bin = bin

    def __init__(self):
        self.bin_list = []

    def append(self, id, bin):
        self.bin_list.append(BinaryArray.Item(id, bin))

    def make_binary(self, align):
        header = binary.Binary()
        body = binary.Binary()
        header.append("I", len(self.bin_list))
        for item in self.bin_list:
            header.append("III", item.id, len(item.bin), len(body))
            body += item.bin
            body.align(align)
        return header + body
