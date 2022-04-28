import datetime
from fastapi import Response
import csv
import io
import calendar

from src.tools.none_tool import ifNone


def export(db, session, filename=None):
    data = query_all(db, session)
    return compose_response(output=writer_data(data=data), session=session, filename=filename)


def export_year(db, session, year: int = None, filename=None):
    year = ifNone(year, current_year())
    until_datetime = last_day_of_month(year, 12)
    since_datetime = prefix_datetime(year, 1)
    data = db.query(session).filter(session.addedAt <= until_datetime).filter(session.addedAt >= since_datetime).all()
    return compose_response(output=writer_data(data=data), session=session, filename=filename)


def export_month_on_year(db, session, year: int = None, month: int = None, day: int = None, filename=None):
    year = ifNone(year, current_year())
    month = ifNone(month, current_month())

    until_datetime = last_day_of_month(year, month)
    since_datetime = prefix_datetime(year, month)
    data = db.query(session).filter(session.addedAt <= until_datetime).filter(session.addedAt >= since_datetime).all()
    return compose_response(output=writer_data(data=data), session=session, filename=filename)


def export_twitter_month_on_year(db, session, year: int = None, month: int = None, day: int = None, filename=None):
    year = ifNone(year, current_year())
    month = ifNone(month, current_month())
    day = ifNone(day, current_day())

    if day == 1:
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1

    until_datetime = last_day_of_month(year, month)
    since_datetime = prefix_datetime(year, month)
    data = db.query(session).filter(session.addedAt <= until_datetime).filter(session.addedAt >= since_datetime).all()
    return compose_response(output=writer_data(data=data), session=session, filename=filename)


def query_all(db, session):
    return db.query(session).all()


def get_filename(session):
    return get_name(session) + "_" + get_date()


def get_name(session):
    return session.__tablename__


def init_header(writer, data):
    writer.writerow(get_header(data))


def get_header(data):
    return list(export_header_property(data[0]).keys()) if len(data) > 0 else None


def writer_data(data):
    output = get_output()
    writer = get_writer(output)
    init_header(writer=writer, data=data)
    writer_content(writer=writer, data=data)
    return output


def writer_content(writer, data):
    for i in data:
        writer.writerow(list(v for k, v in export_header_property(i).items()))


def export_header_property(session):
    if hasattr(session, "export"):
        return session.export
    else:
        columns = session.__table__.columns
        result = {}
        for column in columns:
            column_name = column.name
            result[column_name] = column
        return result


def compose_response(output, session, filename=None):
    output.seek(0)
    response = Response(content=output.read(), media_type="text/csv")
    print(f"attachment; filename={filename if filename is not None else get_filename(session)}.csv")
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename={filename if filename is not None else get_filename(session)}.csv"
    return response


def get_output():
    return io.StringIO()


def get_writer(output):
    return csv.writer(output)


def get_date():
    return datetime.datetime.now().strftime('%Y_%m_%d')


def current_year() -> int:
    return int(current_datetime().strftime('%Y'))


def current_month() -> int:
    return int(current_datetime().strftime('%m'))


def current_day() -> int:
    return int(current_datetime().strftime('%d'))


def current_month_year() -> str:
    return current_datetime().strftime('%Y-%m')


def current_datetime():
    return datetime.datetime.now()


def day_of_month(year: int = None, month: int = None):
    return calendar.monthrange(ifNone(year, current_year()), ifNone(month, current_month()))[1]


def last_day_of_month(year: int = None, month: int = None):
    year = ifNone(year, current_year())
    month = ifNone(month, current_month())
    return datetime.datetime.strptime(
        f"{year}-{month}-{day_of_month(year, month)}  23:59:59",
        "%Y-%m-%d %H:%M:%S")


def last_day_of_year(year: int = None):
    return last_day_of_month(year, month=12)


def prefix_datetime(year: int = None, month: int = None):
    return datetime.datetime.strptime(
        f"{ifNone(year, current_year())}-{ifNone(month, current_month())}-01  00:00:00",
        "%Y-%m-%d %H:%M:%S")
