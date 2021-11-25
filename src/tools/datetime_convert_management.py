from datetime import datetime
import datetime as dt
import pytz


def current_datetime_with_timezone():
    return append_timezone(dt.datetime.now())


def convert_to_utc(target):
    target.replace(tzinfo=pytz.UTC)
    return target


def append_timezone(target, timezone: str = 'Asia/Bangkok'):
    return target.astimezone(pytz.timezone(timezone))


def convert_datetime_to_string(target, timezone: str = 'Asia/Bangkok'):
    return target.astimezone(pytz.timezone(timezone)).strftime("%a %b %d %H:%M:%S %z %Y")


def convert_datetime_to_string_for_backup_mode(target):
    return target.strftime("%Y-%m-%d %H:%M:%S.%f%z")


def convert_string_to_datetime(target, timezone: str = 'Asia/Bangkok'):
    return datetime.strptime(target, "%a %b %d %H:%M:%S %z %Y").astimezone(pytz.timezone(timezone))


def convert_short_string_to_datetime(target, timezone: str = 'Asia/Bangkok'):
    return datetime.strptime(target, '%d-%m-%Y').astimezone(pytz.timezone(timezone))