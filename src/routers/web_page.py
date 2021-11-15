from fastapi import APIRouter, Request

from src.environment.share_environment import templates

router = APIRouter()


@router.get("/pwg")
async def pwg(request: Request):
    return templates.TemplateResponse("security/password_generator/home.html", {"request": request})
