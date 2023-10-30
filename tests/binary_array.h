#pragma once

#include <cstddef>

struct BinaryArray {
  struct Index {
    int id;
    int size;
    int offset;
  };
  int number_of_items;
  Index index[1];

  template <class T>
  void assign_by_index(T*& p, int i) const {
    assert(i >= 0 && i < number_of_items);
    auto top = reinterpret_cast<const std::byte*>(index + number_of_items);
    p = reinterpret_cast<T*>(top + index[i].offset);
  }

  template <class T>
  bool assign_by_id(T*& p, int id) const {
    // TODO: optimize
    for (int i = 0; i < number_of_items; ++i) {
      if (index[i].id == id) {
        assign_by_index(p, i);
        return true;
      }
    }
    return false;
  }
};
