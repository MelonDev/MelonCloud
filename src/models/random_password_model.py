from pydantic import BaseModel


class RandomPasswordModel(BaseModel):
    length: int = 6
    step: int = 3
    stress: bool = True
    lower_weight: int = 2
    upper_weight: int = 1
    numeric_weight: int = 1
    symbols_weight: int = 0


class SimpleRandomPasswordModel(BaseModel):
    length: int = 6
    step: int = 3