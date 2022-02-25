from enum import Enum


class SortingEnum(str, Enum):
    asc = 'asc'
    desc = 'desc'


class SortingTweet(str, Enum):
    ASC = 'ASC'
    DESC = 'DESC'
