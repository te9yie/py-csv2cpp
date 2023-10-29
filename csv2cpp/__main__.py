import argparse
from functools import cmp_to_key
import os
import glob
import csv
import re


TABLE_NAME_R = r"^\[(?P<name>.+)\]$"
TABLE_TAG_R = r"^<(?P<name>.+)>$"


def get_memory_size(var_type: str) -> int:
    """型名のメモリ使用量を取得する"""

    if var_type == "bool":
        return 1
    elif var_type == "int":
        return 4
    elif var_type == "float":
        return 4
    elif var_type == "string":
        return 4

    # テーブル参照
    return 4


class MetaMember:
    """文字列で構成されたメンバー情報"""

    def __init__(self, var_name: str, var_type: str):
        self.var_name: str = var_name
        self.var_type: str = var_type
        self.column_indices: list[int] = []

    def memory_size(self):
        if len(self.column_indices) > 1:
            return 4
        return get_memory_size(self.var_type)


def cmp_var_type(a: MetaMember, b: MetaMember):
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
                        if tag_name == "id":
                            for i, value in enumerate(row[1:]):
                                current_table.set_column_str(i, value)
                        if tag_name == "type":
                            for i, value in enumerate(row[1:]):
                                current_table.set_type_str(i, value)
                        continue
                    # parse row
                    current_table.set_entry(row[0], row[1:])

    def setup_table_ids(self):
        for i, key in enumerate(self.meta_tables):
            table = self.meta_tables[key]
            table.id = i + 1
            table.setup_entry_ids()
            table.setup_members()


def list_csv_files(dir: str) -> list[str]:
    search_path = os.path.join(dir, "**", "*.csv")
    return glob.glob(search_path, recursive=True)


def main():
    parser = argparse.ArgumentParser()
    parser.parse_args()

    files = list_csv_files("./")
    database = MetaDatabase()
    database.parse(files)
    database.setup_table_ids()

    for table_name in database.meta_tables:
        table = database.meta_tables[table_name]
        print("<{}:{}>".format(table.id, table.id_str))
        for m in table.members:
            for i in m.column_indices:
                print("{}:{}".format(table.column_strs[i], table.type_strs[i]), end=" ")
        print()
        for entry in table.entries.values():
            print("{}:{}>".format(entry.id, entry.id_str), end=" ")
            for m in table.members:
                for i in m.column_indices:
                    print("'{}'".format(entry.value_strs[i]), end=" ")
            print()


if __name__ == "__main__":
    main()
