import enum


class VarType(enum.Enum):
    BOOL = enum.auto()
    INT = enum.auto()
    FLOAT = enum.auto()
    STRING = enum.auto()


class Member:
    def __init__(self, var_type: VarType, name: str, length: int = 1):
        self.var_type = var_type
        self.name = name
        self.is_array: bool = length > 1
        self.array_length = length

    def member_strs(self) -> list[str]:
        if self.is_array:
            return [
                "std::size_t {}_offset;".format(self.name),
                "static constexpr std::size_t {}_len = {};".format(
                    self.name, self.array_length
                ),
            ]
        else:
            if self.var_type == VarType.BOOL:
                return self.__member_strs(self.name, "bool")
            elif self.var_type == VarType.INT:
                return self.__member_strs(self.name, "int")
            elif self.var_type == VarType.FLOAT:
                return self.__member_strs(self.name, "float")
            elif self.var_type == VarType.STRING:
                return ["std::size_t {}_offset;".format(self.name)]
        return [""]

    def method_strs(self, indent: str) -> list[str]:
        if self.is_array:
            if self.var_type == VarType.BOOL:
                return self.__array_method_strs(indent, self.name, "bool")
            elif self.var_type == VarType.INT:
                return self.__array_method_strs(indent, self.name, "int")
            elif self.var_type == VarType.FLOAT:
                return self.__array_method_strs(indent, self.name, "float")
            elif self.var_type == VarType.STRING:
                return [
                    "inline const char* {}(std::size_t i) const {{".format(self.name),
                    "{}auto base = reinterpret_cast<const std::byte*>(this);".format(
                        indent
                    ),
                    "{}auto p = base + {}_offset;".format(indent, self.name),
                    "{}auto s_p = reinterpret_cast<const std::size_t*>(p);".format(
                        indent
                    ),
                    "{}return reinterpret_cast<const char*>(base + *(s_p + i));".format(
                        indent
                    ),
                    "}",
                ]
        else:
            if self.var_type == VarType.STRING:
                return [
                    "inline const char* {}(std::size_t i) const {{".format(self.name),
                    "{}auto base = reinterpret_cast<const std::byte*>(this);".format(
                        indent
                    ),
                    "{}auto p = base + {}_offset;".format(indent, self.name),
                    "{}return reinterpret_cast<const char*>(p) + i;".format(indent),
                    "}",
                ]
        return [""]

    def __member_strs(self, name_str: str, type_str: str) -> list[str]:
        return ["{} {};".format(type_str, name_str)]

    def __array_method_strs(
        self, indent: str, name_str: str, type_str: str
    ) -> list[str]:
        return [
            "inline {} {}(std::size_t i) const {{".format(type_str, name_str),
            "{}auto base = reinterpret_cast<const std::byte*>(this);".format(indent),
            "{}auto p = base + {}_offset;".format(indent, name_str),
            "{}return *(reinterpret_cast<const {}*>(p) + i);".format(indent, type_str),
            "}",
        ]


if __name__ == "__main__":
    b = Member(VarType.STRING, "name")
    print(b.method_strs("  "))
