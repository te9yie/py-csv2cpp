import enum


class VarType(enum.Enum):
    BOOL = enum.auto()
    INT = enum.auto()
    FLOAT = enum.auto()
    STRING = enum.auto()


def str_to_var_type(name: str) -> VarType:
    if name == "bool":
        return VarType.BOOL
    elif name == "int":
        return VarType.INT
    elif name == "float":
        return VarType.FLOAT
    elif name == "string":
        return VarType.STRING
    raise ValueError("unkown type: '{}'".format(name))


class Member:
    def __init__(self, name: str, type_str: str):
        self.var_type = str_to_var_type(type_str)
        self.name = name
        self.array_length = 1

    def inc_array_length(self):
        self.array_length += 1

    def member_strs(self) -> list[str]:
        if self.array_length > 1:
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
        if self.array_length > 1:
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
    b = Member("name", "int")
    print(b.member_strs())
