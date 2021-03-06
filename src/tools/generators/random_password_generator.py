import string
import random

from pydantic import BaseModel

from src.models.random_password_model import RandomPasswordModel

_lower = string.ascii_lowercase
_upper = string.ascii_uppercase
_num = string.digits
_symbols = string.punctuation


def _generator(populations, length: int, step: int = None, stress: bool = True) -> str:
    _raw = random.sample(populations, length * (step if step is not None or step != 0 else 1))
    return ("-" if stress else "").join(["".join(_raw[i:i + length]) for i in range(0, len(_raw), length)])


class RandomPasswordGenerator:

    @staticmethod
    def simple(step: int = 3, length: int = 6) -> str:
        lower = string.ascii_lowercase
        lower1 = string.ascii_lowercase
        upper = string.ascii_uppercase
        num = string.digits

        populations = lower + lower1 + upper + num
        return _generator(populations=populations, length=length if length is not None else 6,
                          step=step if step is not None else 3)

    @staticmethod
    def advance(length: int = 6, step: int = 3, stress: bool = True, lower_weight: int = 2, upper_weight: int = 1,
                numeric_weight: int = 1, symbols_weight: int = 0) -> str:

        if (lower_weight + upper_weight + numeric_weight + symbols_weight + symbols_weight) <= 0:
            populations = (_lower * 2) + _upper + _num
        else:
            populations = (_lower * lower_weight) + (_upper * upper_weight) + (_num * numeric_weight) + (
                    _symbols * symbols_weight)

        print(step)
        return _generator(populations=populations, length=length, step=step, stress=stress)

    @staticmethod
    def advance(length: int = 6, step: int = 3, stress: bool = True, lower_weight: int = 2, upper_weight: int = 1,
                numeric_weight: int = 1, symbols_weight: int = 0) -> str:

        if (lower_weight + upper_weight + numeric_weight + symbols_weight + symbols_weight) <= 0:
            populations = (_lower * 2) + _upper + _num
        else:
            populations = (_lower * lower_weight) + (_upper * upper_weight) + (_num * numeric_weight) + (
                    _symbols * symbols_weight)

        return _generator(populations=populations, length=length, step=step, stress=stress)

    @staticmethod
    def custom(request: RandomPasswordModel):
        return RandomPasswordGenerator.advance(length=request.length,
                                               step=request.step,
                                               stress=request.stress,
                                               lower_weight=request.lower_weight,
                                               upper_weight=request.upper_weight,
                                               numeric_weight=request.numeric_weight,
                                               symbols_weight=request.symbols_weight)
