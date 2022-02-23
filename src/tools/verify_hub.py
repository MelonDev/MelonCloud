from os import abort

from fastapi import HTTPException

from src.models.response_model import ResponseModel


def verify_parameters(value, is_empty: bool = None):
    if value is None:
        return False
    if type(value) is int:
        return True
    if type(value) is str:
        if is_empty is None:
            return True
        if is_empty and len(value) >= 0:
            return True
        if not is_empty and len(value) > 0:
            return True

    return False


async def verify_return(data=None, code=None, message=None, content=None):
    if data is not None:
        if code is not None:
            return data, code
        return data
    if code is not None:
        if message is not None:
            return {"message": message}, code
        if content is not None:
            return {"content": content}, code
        raise HTTPException(status_code=code, detail="STATUS_CODE=" + str(code))
    raise HTTPException(status_code=500, detail="Error 500")


def response(data=None, code=None, message=None, content=None):
    if data is not None:
        response = ResponseModel(data=data)
        if code is not None:
            return response, code
        return response
    if code is not None:
        if message is not None:
            return {"message": message}, code
        if content is not None:
            return {"content": content}, code
        raise HTTPException(status_code=code, detail="STATUS_CODE=" + str(code))
    raise HTTPException(status_code=500, detail="Error 500")
