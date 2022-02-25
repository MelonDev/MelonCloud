import json

import pyxtension
from pyxtension.Json import Json


def has_key(value):
    return value != {}


def to_json_object(value: dict) -> pyxtension.Json.Json:
    return Json(value)


def pretty_json(value: dict) -> str:
    return json.dumps(value, indent=4)
