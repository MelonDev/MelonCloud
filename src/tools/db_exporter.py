import uuid
import datetime
from fastapi import HTTPException, status, Response
from sqlalchemy.dialects.postgresql import UUID

import csv
import io

from sqlalchemy import Text, DateTime as SQLDateTime, ARRAY

from src.tools.converters.datetime_converter import convert_datetime_to_string_for_backup_mode
from src.tools.converters.list_converter import list_to_set


def export(db, session, filename=None):
    data = query_all(db, session)
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
