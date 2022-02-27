import calendar
import datetime as dt


def today():
    return dt.date.today()


def first_day_of_month(month=None, year=None):
    day = today()
    if month is not None:
        day = day.replace(month=month)
    if year is not None:
        day = day.replace(year=year)

    if day.day < 3:
        day -= dt.timedelta(days=7)

    return day.replace(day=1)


def first_day_of_month_with_time(month=None, year=None):
    day = first_day_of_month(month=month, year=year)
    return dt.datetime.combine(day, dt.time.min)


def days_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def last_day_of_month(month=None, year=None):
    first_day = first_day_of_month(month, year)
    monthrange = days_of_month(first_day.year, first_day.month)
    return first_day.replace(day=monthrange)


def last_day_of_month_with_time(month=None, year=None):
    last_day = last_day_of_month(month, year)
    return dt.datetime.combine(last_day, dt.time.max)


def previous_month(date):
    date -= dt.timedelta(days=days_of_month(date.year, date.month))
    return date


def first_day_of_previous_month(month=None, year=None):
    day = first_day_of_month(month, year)
    day = previous_month(day)
    return day.replace(day=1)


def first_day_of_previous_month_with_time(month=None, year=None):
    day = first_day_of_previous_month(month=month, year=year)
    return dt.datetime.combine(day, dt.time.min)


def last_day_of_previous_month(month=None, year=None):
    day = first_day_of_previous_month(month, year)
    monthrange = days_of_month(day.year, day.month)
    return day.replace(day=monthrange)


def last_day_of_previous_month_with_time(month=None, year=None):
    last_day = last_day_of_previous_month(month, year)
    return dt.datetime.combine(last_day, dt.time.max)


def next_month(date):
    date += dt.timedelta(days=days_of_month(date.year, date.month))
    return date


def first_day_of_next_month(month=None, year=None):
    day = first_day_of_month(month, year)
    day = next_month(day)
    return day.replace(day=1)


def first_day_of_next_month_with_time(month=None, year=None):
    day = first_day_of_next_month(month=month, year=year)
    return dt.datetime.combine(day, dt.time.min)


def last_day_of_next_month(month=None, year=None):
    day = first_day_of_next_month(month, year)
    monthrange = days_of_month(day.year, day.month)
    return day.replace(day=monthrange)


def last_day_of_next_month_with_time(month=None, year=None):
    last_day = last_day_of_next_month(month, year)
    return dt.datetime.combine(last_day, dt.time.max)


def first_day_of_year(year=None):
    day = today()
    if year is not None:
        day = day.replace(year=year)
    return day.replace(month=1, day=1)


def last_day_of_year(year=None):
    day = today()
    if year is not None:
        day = day.replace(year=year)
    return day.replace(month=12, day=31)


def previous_year(date):
    date -= dt.timedelta(days=365)
    return date

