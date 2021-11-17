from fastapi import APIRouter, Request

from src.environment.share_environment import templates
from src.tools.random_password_generator import RandomPasswordGenerator, SimpleRandomPasswordModel

router = APIRouter()


@router.get("/pwg", include_in_schema=False)
async def pwg(request: Request, step: int = None):
    generator = RandomPasswordGenerator()
    password = generator.simple(step=step) if step is not None else generator.simple()
    return templates.TemplateResponse("security/password_generator/home.html",
                                      {"request": request, "password": password})


@router.get("/test", include_in_schema=False)
async def test(request: Request):
    return templates.TemplateResponse("example/test-bootstrap.html",
                                      {"request": request})
