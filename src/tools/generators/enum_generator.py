from typing import Tuple

import enum


def make_enum(name: str, values):
    data = []
    for i in values:
        if type(i) is tuple:
            data.append(i)
        if type(i) is str:
            data.append((i, i))
    return enum.Enum(name, dict(data))
