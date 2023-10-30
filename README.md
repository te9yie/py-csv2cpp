# csv2cpp

CSVファイルからC++のヘッダファイルとバイナリを生成する

## Usage

```txt
python -m csv2cpp -i tests/csv -oh csv.h -ob csv.bin
```

```txt
usage: csv2cpp [-h] [-i INPUT_DIR] [-oh OUTPUT_HEADER] [-ob OUTPUT_BIN]

options:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input-dir INPUT_DIR
  -oh OUTPUT_HEADER, --output-header OUTPUT_HEADER
  -ob OUTPUT_BIN, --output-bin OUTPUT_BIN
```

## CSV

```csv
[`テーブル名`]
<column>,...  # カラム名（メンバ変数名）
<type>,...    # 変数の型
`ID1`,...     # IDごとの定義を並べる
`ID2`,...
```

例: [tests/csv/basic.csv](tests/csv/basic.csv)

```csv
[Basic]
<column>,name,age,weight,can_battle,skill,skill,friends,friends
<type>,string,int,float,bool,Skill,Skill,string,string
alice,"Alice",24,58.5,true,FireBall,,"Carol","Dave"
bob,"Bob",32,84.5,false
```

### 出力ヘッダ

```cpp

struct Basic {
  int name_offset;
  int age;
  float weight;
  static constexpr int skill_len = 2;
  int skill[2];
  static constexpr int friends_len = 2;
  int friends_offset[2];
  bool can_battle;

  const char* name() const {
    auto top = reinterpret_cast<const std::byte*>(this + 1);
    return reinterpret_cast<const char*>(top + name_offset);
  }
  const char* friends(std::size_t i) const {
    auto top = reinterpret_cast<const std::byte*>(this + 1);
    return reinterpret_cast<const char*>(top + friends_offset[i]);
  }
};
```

[tests/csv.h](tests/csv.h)

### 対応している型

- bool
- int
- float
- string
- 他のテーブルへの参照
- id (バイナリはIDの順に並ぶ)
- comment, # (コメント)

`id` はIDを固定したり、バイナリの出力順を指定したいときに使う。
セーブファイルにIDを保存したりする場合は固定しておかないと行を追加した場合にずれる可能性がある。

## 読み込み方

```cpp
const char* bin_data;
...
auto bin = reinterpret_cast<const BinaryArray*>(bin_data);

const BinaryArray* basic_table_p = nullptr;
bin->assign_by_id(basic_table_p, generated::TABLE_Basic);

const generated::Basic* basic_p = nullptr;
basic_table_p->assign_by_id(basic_p, generated::BASIC_alice);

basic_p->name();
basic_p->age;
...
```

[tests/test_csv2cpp.cpp](tests/test_csv2cpp.cpp)
