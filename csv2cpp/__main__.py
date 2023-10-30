from __future__ import annotations
import argparse
from functools import cmp_to_key
import os
import glob
import csv
import re
import sys

from csv2cpp.binary import Binary
from csv2cpp.binary_array import BinaryArray


PACK_ALIGN = 4
INDENT = "  "
NAMESPACE = "generated"
TABLE_NAME_R = r"^\[(?P<name>.+)\]$"
TABLE_COLUMN_R = r"^<(?P<name>.+)>$"


def is_ignore_type(var_type: str) -> bool:
    """出力時に無視する型"""

    if var_type == "id" or var_type == "comment" or var_type == "#":
        return True
    return False


def get_memory_size(var_type: str) -> int:
    """型のメモリ使用量を取得する"""

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


def str_to_bool(s: str) -> bool:
    return s.lower() in ["true", "on", "yes", "t", "y", "o"]


def make_member_strs(
    var_name: str, var_type: str, length: int, suffix: str = ""
) -> list[str]:
    """メンバ変数の定義文字列をつくる"""

    if length > 1:
        return [
            f"static constexpr int {var_name}_len = {length};",
            f"{var_type} {var_name}{suffix}[{length}];",
        ]
    else:
        return [f"{var_type} {var_name}{suffix};"]


class StringBin:
    """文字列バイナリパック"""

    def __init__(self):
        self.bin: Binary = Binary()
        self.index: dict[str, int] = {}
        self.append("")

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
        """メンバ定義文字列を返す"""

        if is_ignore_type(self.var_type):
            return []
        if (
            self.var_type == "bool"
            or self.var_type == "int"
            or self.var_type == "float"
        ):
            return make_member_strs(
                self.var_name, self.var_type, len(self.column_indices)
            )
        if self.var_type == "string":
            return make_member_strs(
                self.var_name, "int", len(self.column_indices), "_offset"
            )
        return make_member_strs(self.var_name, "int", len(self.column_indices))

    def method_strs(self, indent: str) -> list[str]:
        """メソッド定義文字列を返す"""

        if is_ignore_type(self.var_type):
            return []
        if self.var_type == "string":
            if self.is_array():
                return [
                    f"const char* {self.var_name}(std::size_t i) const {{",
                    f"{indent}auto top = reinterpret_cast<const std::byte*>(this + 1);",
                    f"{indent}return reinterpret_cast<const char*>(top + {self.var_name}_offset[i]);",
                    "}",
                ]
            else:
                return [
                    f"const char* {self.var_name}() const {{",
                    f"{indent}auto top = reinterpret_cast<const std::byte*>(this + 1);",
                    f"{indent}return reinterpret_cast<const char*>(top + {self.var_name}_offset);",
                    "}",
                ]
        return []


def cmp_var_type(a: MetaMember, b: MetaMember) -> int:
    """メモリサイズでソートするための比較関数"""

    a_size = a.memory_size()
    b_size = b.memory_size()
    if a_size < b_size:
        return 1
    if a_size > b_size:
        return -1
    return 0


def cmp_entry_id(a: MetaEntry, b: MetaEntry) -> int:
    """EntryのIDでソートするための比較関数"""

    if a.id < b.id:
        return -1
    if a.id > b.id:
        return 1
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
                str_bin.append(self.value_strs[i] if i < len(self.value_strs) else "")
        return str_bin

    def make_bin(self, table: MetaTable, database: MetaDatabase) -> Binary:
        bin = Binary()
        str_bin: StringBin = self.__make_string_bin(table)
        str_bin.align(PACK_ALIGN)
        for member in table.members:
            if is_ignore_type(member.var_type):
                continue
            for i in member.column_indices:
                value = self.value_strs[i] if i < len(self.value_strs) else None
                if member.var_type == "bool":
                    bin.append("?", str_to_bool(value if value else "False"))
                elif member.var_type == "int":
                    bin.append("i", int(value if value else "0"))
                elif member.var_type == "float":
                    bin.append("f", float(value if value else "0"))
                elif member.var_type == "string":
                    bin.append("i", str_bin.get_index(value if value else ""))
                else:
                    bin.append(
                        "i",
                        database.get_entry_id(member.var_type, value) if value else 0,
                    )
        bin.align(PACK_ALIGN)
        bin += str_bin.bin
        return bin


class MetaTable:
    """文字列で構成されたテーブル情報"""

    def __init__(self, id_str: str):
        self.id: int = 0
        self.id_str = id_str
        self.column_strs: list[str] = []
        self.type_strs: list[str] = []
        self.members: list[MetaMember] = []
        self.entries: list[MetaEntry] = []
        self.entry_dict: dict[str, MetaEntry] = {}
        self.has_id_column: bool = False

    def is_enum(self) -> bool:
        return len(self.column_strs) == 0

    def set_column_str(self, i: int, value: str):
        if len(self.column_strs) >= i:
            self.column_strs.extend([""] * (i - len(self.column_strs) + 1))
        self.column_strs[i] = value

    def set_type_str(self, i: int, value: str):
        if len(self.type_strs) >= i:
            self.type_strs.extend([""] * (i - len(self.type_strs) + 1))
        self.type_strs[i] = value

    def add_entry(self, id_str: str, values: list[str]):
        entry = MetaEntry(id_str)
        entry.value_strs = values
        self.entries.append(entry)
        self.entry_dict.setdefault(id_str, entry)

    def setup_members(self):
        member_map: dict[str, MetaMember] = {}

        for i in range(len(self.column_strs)):
            var_name = self.column_strs[i]
            var_type = self.type_strs[i]

            if var_type == "id":
                self.has_id_column = True

            member = member_map.setdefault(var_name, MetaMember(var_name, var_type))
            member.column_indices.append(i)

        self.members = list(member_map.values())
        self.members.sort(key=cmp_to_key(cmp_var_type))

    def __id_column_index(self):
        for member in self.members:
            if member.var_type == "id":
                return member.column_indices[0]
        raise KeyError("not found id column")

    def setup_entry_ids(self):
        if self.has_id_column:
            i = self.__id_column_index()
            for entry in self.entries:
                id = entry.value_strs[i]
                if id == "":
                    raise ValueError(f"id is not set: {self.id_str}::{entry.id_str}")
                entry.id = int(id)
        else:
            for i, entry in enumerate(self.entries):
                entry.id = i + 1
        self.entries.sort(key=cmp_to_key(cmp_entry_id))

    def id_strs(self, end: str) -> list[str]:
        strs: list[str] = []
        for entry in self.entries:
            if entry.id_str == "":
                continue
            strs += [f"{entry.id_str} = {entry.id}{end}"]
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
        if self.is_enum():
            print(f"enum {self.id_str} {{")
            print(
                os.linesep.join(
                    [
                        f"{INDENT}{self.id_str.upper()}_{line}"
                        for line in self.id_strs(",")
                    ]
                )
            )
            print("};")
            print()
        else:
            print(f"struct {self.id_str} {{")
            members = self.member_strs()
            if len(members) > 0:
                print(
                    os.linesep.join([f"{INDENT}{line}" for line in self.member_strs()])
                )
            methods = self.method_strs(INDENT)
            if len(methods) > 0:
                print()
                print(
                    os.linesep.join(
                        [f"{INDENT}{line}" for line in self.method_strs(INDENT)]
                    )
                )
            print("};")
            print()
            print(f"enum {self.id_str}Id {{")
            print(
                os.linesep.join(
                    [
                        f"{INDENT}{self.id_str.upper()}_{line}"
                        for line in self.id_strs(",")
                    ]
                )
            )
            print("};")
            print()

    def make_bin(self, database: MetaDatabase) -> Binary:
        bin = BinaryArray()
        for entry in self.entries:
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
                    if row[0].startswith("#"):
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
                    r = re.fullmatch(TABLE_COLUMN_R, row[0])
                    if r:
                        tag_name = r.group("name")
                        if tag_name == "column":
                            for i, value in enumerate(row[1:]):
                                current_table.set_column_str(i, value)
                        if tag_name == "type":
                            for i, value in enumerate(row[1:]):
                                current_table.set_type_str(i, value)
                        continue
                    # parse row
                    current_table.add_entry(row[0], row[1:])

    def get_entry_id(self, table_name: str, entry_name: str) -> int:
        if table_name not in self.meta_tables:
            raise KeyError(f"not found table name: {table_name}")
        table = self.meta_tables[table_name]
        if entry_name not in table.entry_dict:
            raise KeyError(f"not found table name: {table_name}")
        entry = table.entry_dict[entry_name]
        return entry.id

    def setup_table(self):
        for i, key in enumerate(self.meta_tables):
            table = self.meta_tables[key]
            table.id = i + 1
            table.setup_members()
            table.setup_entry_ids()

    def __make_header(self):
        print("#pragma once")
        print()
        print("#include <cstddef>")
        print()
        print(f"namespace {NAMESPACE} {{")
        print()
        print("enum TableId {")
        for table_name in self.meta_tables:
            table = self.meta_tables[table_name]
            if table.is_enum():
                continue
            print(f"{INDENT}TABLE_{table_name} = {table.id},")
        print("};")
        print()
        for table_name in self.meta_tables:
            table = self.meta_tables[table_name]
            table.output_cpp_header()
        print("}")

    def __make_bin(self) -> Binary:
        bin = BinaryArray()
        for table_name in self.meta_tables:
            table = self.meta_tables[table_name]
            if table.is_enum():
                continue
            bin.append(table.id, table.make_bin(self))
        return bin.make_binary(PACK_ALIGN)

    def output_header(self, path: str):
        if path == "":
            self.__make_header()
        else:
            with open(path, "w") as f:
                sys.stdout = f
                self.__make_header()
                sys.stdout = sys.__stdout__

    def output_bin(self, path: str):
        bin = self.__make_bin()
        with open(path, "wb") as f:
            bin.tofile(f)


def list_csv_files(dir: str) -> list[str]:
    search_path = os.path.join(dir, "**", "*.csv")
    return glob.glob(search_path, recursive=True)


def main():
    parser = argparse.ArgumentParser(prog="csv2cpp")
    parser.add_argument("-i", "--input-dir")
    parser.add_argument("-oh", "--output-header")
    parser.add_argument("-ob", "--output-bin")
    args = parser.parse_args()

    files = list_csv_files(args.input_dir if args.input_dir else "")
    database = MetaDatabase()
    database.parse(files)
    database.setup_table()

    database.output_header(args.output_header if args.output_header else "")
    if args.output_bin:
        database.output_bin(args.output_bin)


if __name__ == "__main__":
    main()
