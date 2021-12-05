import datetime
from typing import Any

from src.tools.converters.datetime_converter import current_datetime_with_timezone

class ResponseModel:
    timestamp: datetime
    data: Any

    def __init__(self, data, force_str=False):
        self.timestamp = current_datetime_with_timezone()
        self.data = str(data) if force_str else data
