#pragma once

#include <cstddef>

struct BinaryArray {
  struct Index {
    int id;
    int size;
    int offset;
  };
  int item_count;
  Index index[1];

  template <class T>
  void assign_by_index(T*& p, int i) const {
    assert(i >= 0 && i < item_count);
    auto top = reinterpret_cast<const std::byte*>(index + item_count);
    p = reinterpret_cast<T*>(top + index[i].offset);
  }

  template <class T>
  bool assign_by_id(T*& p, int id, int* out_index = nullptr) const {
    // TODO: optimize
    for (int i = 0; i < item_count; ++i) {
      if (index[i].id == id) {
        assign_by_index(p, i);
        if (out_index) {
          *out_index = i;
        }
        return true;
      }
    }
    return false;
  }
};
