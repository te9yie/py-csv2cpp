#pragma once

#include <cstddef>

namespace generated {

enum TableId {
  TABLE_Basic = 1,
  TABLE_Skill = 2,
  TABLE_item = 3,
  TABLE_NoLabel = 5,
};

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

enum BasicId {
  BASIC_alice = 1,
  BASIC_bob = 2,
};

struct Skill {
  int name_offset;

  const char* name() const {
    auto top = reinterpret_cast<const std::byte*>(this + 1);
    return reinterpret_cast<const char*>(top + name_offset);
  }
};

enum SkillId {
  SKILL_FireBall = 1,
  SKILL_ThunderStorm = 2,
};

struct item {
  int name_offset;

  const char* name() const {
    auto top = reinterpret_cast<const std::byte*>(this + 1);
    return reinterpret_cast<const char*>(top + name_offset);
  }
};

enum itemId {
  ITEM_potion = 100,
  ITEM_cure_leaf = 101,
};

enum Count {
  COUNT_ONE = 1,
  COUNT_TWO = 2,
  COUNT_THREE = 3,
};

struct NoLabel {
  int value;
  bool enable;
};

enum NoLabelId {
  NOLABEL_First = 10,
  NOLABEL_Second = 20,
};

}
