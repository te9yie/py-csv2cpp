import argparse
import os
import glob
import csv
import re


TABLE_NAME_R = r"^\[(?P<name>.+)\]$"
TABLE_TAG_R = r"^<(?P<name>.+)>$"


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
        for i, column in enumerate(table.column_strs):
            print("{}:{}".format(table.column_strs[i], table.type_strs[i]), end=" ")
        print()
        for entry in table.entries.values():
            print("{}:{}>".format(entry.id, entry.id_str), end=" ")
            for column in entry.value_strs:
                print(column, end=" ")
            print()


if __name__ == "__main__":
    main()
