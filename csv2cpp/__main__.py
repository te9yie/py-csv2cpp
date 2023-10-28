import argparse
import os
import glob
import csv
import re


TABLE_NAME_R = r"^\[(?P<name>.+)\]$"
TABLE_TAG_R = r"^<(?P<name>.+)>$"


class MetaEntry:
    """文字列で構成されたエントリー情報"""

    def __init__(self, id: str):
        self.id = id
        self.values: list[str] = []


class MetaTable:
    """文字列で構成されたテーブル情報"""

    def __init__(self, name: str):
        self.name = name
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
        entry.values = values


class Database:
    def __init__(self, csv_files: list[str]) -> None:
        self.csv_files = csv_files
        self.meta_tables: dict[str, MetaTable] = {}

    def parse(self):
        for path in self.csv_files:
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


def list_csv_files(dir: str) -> list[str]:
    search_path = os.path.join(dir, "**", "*.csv")
    return glob.glob(search_path, recursive=True)


def main():
    parser = argparse.ArgumentParser()
    parser.parse_args()

    files = list_csv_files("./")
    database = Database(files)
    database.parse()

    for table_name in database.meta_tables:
        table = database.meta_tables[table_name]
        print()
        print("<{}>".format(table.name))
        for i, column in enumerate(table.column_strs):
            print("{}:{}".format(table.column_strs[i], table.type_strs[i]), end=" ")
        for entry in table.entries.values():
            print()
            print("{}:".format(entry.id), end=" ")
            for column in entry.values:
                print(column, end=" ")


if __name__ == "__main__":
    main()
