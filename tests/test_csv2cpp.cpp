#include <gtest/gtest.h>
#include <fstream>
#include <iostream>
#include <vector>
#include "binary_array.h"
#include "csv.h"

namespace {

class Csv2CppTest : public testing::Test {
 public:
  std::vector<char> csv_bin;

 protected:
  virtual void SetUp() {
    std::ifstream in("csv.bin", std::ios::binary);
    ASSERT_TRUE(in);
    csv_bin.assign(std::istreambuf_iterator<char>(in),
                   std::istreambuf_iterator<char>());
  }
};

TEST_F(Csv2CppTest, Table) {
  auto bin = reinterpret_cast<const BinaryArray*>(csv_bin.data());
  EXPECT_EQ(bin->item_count, 2);
}

TEST_F(Csv2CppTest, Basic) {
  auto bin = reinterpret_cast<const BinaryArray*>(csv_bin.data());

  const BinaryArray* basic_table_p = nullptr;
  EXPECT_TRUE(bin->assign_by_id(basic_table_p, generated::TABLE_Basic));

  const generated::Basic* basic_p = nullptr;
  {
    EXPECT_TRUE(basic_table_p->assign_by_id(basic_p, generated::BASIC_alice));
    EXPECT_STREQ(basic_p->name(), "Alice");
    EXPECT_EQ(basic_p->age, 24);
    EXPECT_FLOAT_EQ(basic_p->weight, 58.5);
    EXPECT_TRUE(basic_p->can_battle);
    EXPECT_EQ(basic_p->skill[0], generated::SKILL_FireBall);
    EXPECT_EQ(basic_p->skill[1], 0);
    EXPECT_STREQ(basic_p->friends(0), "Carol");
    EXPECT_STREQ(basic_p->friends(1), "Dave");
  }
  {
    EXPECT_TRUE(basic_table_p->assign_by_id(basic_p, generated::BASIC_bob));
    EXPECT_STREQ(basic_p->name(), "Bob");
    EXPECT_EQ(basic_p->age, 32);
    EXPECT_FLOAT_EQ(basic_p->weight, 84.5);
    EXPECT_FALSE(basic_p->can_battle);
    EXPECT_EQ(basic_p->skill[0], 0);
    EXPECT_EQ(basic_p->skill[1], 0);
    EXPECT_STREQ(basic_p->friends(0), "");
    EXPECT_STREQ(basic_p->friends(1), "");
  }
}

}  // namespace
