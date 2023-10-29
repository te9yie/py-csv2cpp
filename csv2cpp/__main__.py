from __future__ import annotations
import argparse
from functools import cmp_to_key
import os
import glob
import csv
import re

from .binary import Binary
from .binary_array import BinaryArray


PACK_ALIGN = 4
TABLE_NAME_R = r"^\[(?P<name>.+)\]$"
TABLE_TAG_R = r"^<(?P<name>.+)>$"


def is_ignore_type(var_type: str) -> bool:
    if var_type == "id" or var_type == "comment":
        return True
    return False


def get_memory_size(var_type: str) -> int:
    """型名のメモリ使用量を取得する"""

    if is_ignore_type(var_type):
        return 0
    elif var_type == "bool":
        return 1
    elif var_type == "int":
        return 4
    elif var_type == "float":
        return 4
    elif var_type == "string":
        return 4

    # テーブル参照
    return 4


def str_to_bool(value: str) -> bool:
    if value.lower() == "true" or value == "o" or value == "1":
        return True
    return False


class StringBin:
    def __init__(self):
        self.bin: Binary = Binary()
        self.index: dict[str, int] = {}

    def append(self, s: str):
        self.index[s] = len(self.bin)
        self.bin.append_string(s)

    def align(self, align: int):
        self.bin.align(align)

    def get_index(self, s: str) -> int:
        if s not in self.index:
            raise KeyError(f"not found string: {s}")
        return self.index[s]


class MetaMember:
    """文字列で構成されたメンバー情報"""

    def __init__(self, var_name: str, var_type: str):
        self.var_name: str = var_name
        self.var_type: str = var_type
        self.column_indices: list[int] = []

    def is_array(self) -> bool:
        return len(self.column_indices) > 1

    def memory_size(self) -> int:
        if is_ignore_type(self.var_type):
            return 0
        if self.is_array():
            return 4
        return get_memory_size(self.var_type)

    def member_strs(self) -> list[str]:
        if is_ignore_type(self.var_type):
            return []
        if self.is_array():
            return [f"int {self.var_name}_offset;", f"int {self.var_name}_len;"]
        else:
            if self.var_type == "bool":
                return [f"bool {self.var_name};"]
            if self.var_type == "int":
                return [f"int {self.var_name};"]
            if self.var_type == "float":
                return [f"float {self.var_name};"]
            if self.var_type == "string":
                return [f"int {self.var_name}_offset;"]
        return [f"int {self.var_name};"]

    def method_strs(self, indent: str) -> list[str]:
        if is_ignore_type(self.var_type):
            return []
        if self.is_array():
            if (
                self.var_type == "bool"
                or self.var_type == "int"
                or self.var_type == "float"
            ):
                return self.__array_method_strs(indent, self.var_name, self.var_type)
            elif self.var_type == "string":
                return [
                    f"const char* {self.var_name}(std::size_t i) const {{",
                    f"{indent}auto top = reinterpret_cast<const std::byte*>(this);",
                    f"{indent}auto s_top = reinterpret_cast<const int*>(top + {self.var_name}_offset);",
                    f"{indent}return reinterpret_cast<const char*>(s_top + i);",
                    "}",
                ]
            return self.__array_method_strs(indent, self.var_name, "int")
        else:
            if self.var_type == "string":
                return [
                    f"const char* {self.var_name}() const {{",
                    f"{indent}auto top = reinterpret_cast<const std::byte*>(this);",
                    f"{indent}return reinterpret_cast<const char*>(top + {self.var_name}_offset);",
                    "}",
                ]
        return []

    def __array_method_strs(
        self, indent: str, var_name: str, var_type: str
    ) -> list[str]:
        return [
            f"{var_type} {var_name}(std::size_t i) const {{",
            f"{indent}auto top = reinterpret_cast<const std::byte*>(this);",
            f"{indent}return *(reinterpret_cast<const {var_type}*>(top + {var_name}_offset) + i);",
            "}",
        ]


def cmp_var_type(a: MetaMember, b: MetaMember) -> int:
    a_size = a.memory_size()
    b_size = b.memory_size()
    if a_size < b_size:
        return 1
    if a_size > b_size:
        return -1
    return 0


class MetaEntry:
    """文字列で構成されたエントリー情報"""

    def __init__(self, id_str: str):
        self.id: int = 0
        self.id_str = id_str
        self.value_strs: list[str] = []

    def __make_string_bin(self, table: MetaTable) -> StringBin:
        str_bin: StringBin = StringBin()
        for member in table.members:
            if member.var_type != "string":
                continue
            for i in member.column_indices:
                str_bin.append(self.value_strs[i])
        return str_bin

    def make_bin(self, table: MetaTable, database: MetaDatabase) -> Binary:
        bin = Binary()
        str_bin: StringBin = self.__make_string_bin(table)
        str_bin.align(PACK_ALIGN)
        ext_bin = Binary()
        ext_bin += str_bin.bin
        for member in table.members:
            if is_ignore_type(member.var_type):
                continue
            if member.is_array():
                bin.append("I", len(ext_bin))
                array_bin = Binary()
                for i in member.column_indices:
                    value = self.value_strs[i]
                    if member.var_type == "bool":
                        array_bin.append("?", str_to_bool(value))
                    elif member.var_type == "int":
                        array_bin.append("i", int(value))
                    elif member.var_type == "float":
                        array_bin.append("f", float(value))
                    elif member.var_type == "string":
                        array_bin.append("i", str_bin.get_index(value))
                    else:
                        array_bin.append(
                            "i", database.get_entry_id(member.var_type, value)
                        )
                array_bin.align(PACK_ALIGN)
                ext_bin += array_bin
            else:
                for i in member.column_indices:
                    value = self.value_strs[i]
                    if member.var_type == "bool":
                        bin.append("?", str_to_bool(value))
                    elif member.var_type == "int":
                        bin.append("i", int(value))
                    elif member.var_type == "float":
                        bin.append("f", float(value))
                    elif member.var_type == "string":
                        bin.append("i", str_bin.get_index(value))
                    else:
                        bin.append("i", database.get_entry_id(member.var_type, value))
        bin += ext_bin
        return bin


class MetaTable:
    """文字列で構成されたテーブル情報"""

    def __init__(self, id_str: str):
        self.id: int = 0
        self.id_str = id_str
        self.column_strs: list[str] = []
        self.type_strs: list[str] = []
        self.entries: dict[str, MetaEntry] = {}
        self.members: list[MetaMember] = []

    def set_column_str(self, i: int, value: str):
        if len(self.column_strs) >= i:
            self.column_strs.extend([""] * (i - len(self.column_strs) + 1))
        self.column_strs[i] = value

    def set_type_str(self, i: int, value: str):
        if len(self.type_strs) >= i:
            self.type_strs.extend([""] * (i - len(self.type_strs) + 1))
        self.type_strs[i] = value

    def set_entry(self, id: str, values: list[str]):
        entry = self.entries.setdefault(id, MetaEntry(id))
        entry.value_strs = values

    def setup_entry_ids(self):
        for i, key in enumerate(self.entries):
            self.entries[key].id = i + 1

    def setup_members(self):
        member_map: dict[str, MetaMember] = {}

        for i in range(len(self.column_strs)):
            var_name = self.column_strs[i]
            var_type = self.type_strs[i]
            member = member_map.setdefault(var_name, MetaMember(var_name, var_type))
            member.column_indices.append(i)

        self.members = list(member_map.values())
        self.members.sort(key=cmp_to_key(cmp_var_type))

    def id_strs(self) -> list[str]:
        strs: list[str] = []
        for entry_name in self.entries:
            entry = self.entries[entry_name]
            strs += [f"{entry_name} = {entry.id}"]
        return strs

    def member_strs(self) -> list[str]:
        strs: list[str] = []
        for member in self.members:
            lines = member.member_strs()
            strs += [line for line in lines if line != ""]
        return strs

    def method_strs(self, indent: str) -> list[str]:
        strs: list[str] = []
        for member in self.members:
            lines = member.method_strs(indent)
            strs += [line for line in lines if line != ""]
        return strs

    def output_cpp_header(self):
        if len(self.column_strs) > 0:
            print(f"struct {self.id_str} {{")
            print(os.linesep.join(["  " + line for line in self.member_strs()]))
            print()
            print(os.linesep.join(["  " + line for line in self.method_strs("  ")]))
            print("};")
        else:
            print(f"enum class {self.id_str} {{")
            print(os.linesep.join(["  " + line for line in self.id_strs()]))
            print("};")
        print()

    def make_bin(self, database: MetaDatabase) -> Binary:
        bin = BinaryArray()
        for entry_name in self.entries:
            entry = self.entries[entry_name]
            bin.append(entry.id, entry.make_bin(self, database))
        return bin.make_binary(PACK_ALIGN)


class MetaDatabase:
    def __init__(self):
        self.meta_tables: dict[str, MetaTable] = {}

    def parse(self, csv_files: list[str]):
        for path in csv_files:
            with open(path) as f:
                current_table: MetaTable | None = None
                for row in csv.reader(f):
                    if len(row) == 0:
                        continue
                    r = re.fullmatch(TABLE_NAME_R, row[0])
                    # parse table
                    if r:
                        table_name = r.group("name")
                        table = self.meta_tables.setdefault(
                            table_name, MetaTable(table_name)
                        )
                        current_table = table
                        continue
                    if not current_table:
                        continue
                    # parse tags
                    r = re.fullmatch(TABLE_TAG_R, row[0])
                    if r:
                        tag_name = r.group("name")
                        if tag_name == "name":
                            for i, value in enumerate(row[1:]):
                                current_table.set_column_str(i, value)
                        if tag_name == "type":
                            for i, value in enumerate(row[1:]):
                                current_table.set_type_str(i, value)
                        continue
                    # parse row
                    current_table.set_entry(row[0], row[1:])

    def get_entry_id(self, table_name: str, entry_name: str) -> int:
        if table_name not in self.meta_tables:
            raise KeyError(f"not found table name: {table_name}")
        table = self.meta_tables[table_name]
        if entry_name not in table.entries:
            raise KeyError(f"not found table name: {table_name}")
        entry = table.entries[entry_name]
        return entry.id

    def setup_table(self):
        for i, key in enumerate(self.meta_tables):
            table = self.meta_tables[key]
            table.id = i + 1
            table.setup_entry_ids()
            table.setup_members()

    def output_cpp_header(self):
        print("#pragma once")
        print()
        print("#include <cstddef>")
        print()
        print("namespace generated {")
        print()
        for table_name in self.meta_tables:
            table = self.meta_tables[table_name]
            table.output_cpp_header()
        print("}")

    def make_bin(self) -> Binary:
        bin = BinaryArray()
        for table_name in self.meta_tables:
            table = self.meta_tables[table_name]
            bin.append(table.id, table.make_bin(self))
        return bin.make_binary(PACK_ALIGN)


def list_csv_files(dir: str) -> list[str]:
    search_path = os.path.join(dir, "**", "*.csv")
    return glob.glob(search_path, recursive=True)


def main():
    parser = argparse.ArgumentParser()
    parser.parse_args()

    files = list_csv_files("./")
    database = MetaDatabase()
    database.parse(files)
    database.setup_table()

    database.output_cpp_header()
    bin = database.make_bin()

    with open("csv.bin", "wb") as f:
        bin.tofile(f)


if __name__ == "__main__":
    main()
