import datetime
from typing import Any

from src.tools.converters.datetime_converter import current_datetime_with_timezone


class ResponseModel:
    timestamp: datetime
    data: Any

    def __init__(self, data, force_str=False):
        self.timestamp = current_datetime_with_timezone()
        self.data = str(data) if force_str else data


class ResponsePageModel(ResponseModel):
    total_page: int = None
    page: int = None
    rows: int = None
    limit :int = None

    def __init__(self, rows, data, page, total_page,limit, force_str=False):
        super().__init__(data, force_str)
        self.total_page = total_page if total_page is not None else 1
        self.rows = rows if rows is not None else 1
        self.page = page if page is not None else 1
        self.limit = limit if limit is not None else 1

