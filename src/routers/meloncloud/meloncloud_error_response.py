from fastapi import HTTPException
from fastapi import APIRouter, Depends, HTTPException, status as code, Response


def bad_request_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_400_BAD_REQUEST,
        detail=message if message is not None else "BAD REQUEST")


def not_found_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_404_NOT_FOUND,
        detail=message if message is not None else "NOT FOUND")


def duplicate_on_database_exception(message=None):
    raise HTTPException(
        status_code=code.HTTP_302_FOUND,
        detail=message if message is not None else "TWITTER USER IS EXISTS ON DATABASE")
