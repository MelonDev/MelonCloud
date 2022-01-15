from fastapi import APIRouter, Request

from src.environment.share_environment import templates
from src.tools.generators.random_password_generator import RandomPasswordGenerator

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


@router.get("/pwg_v2", include_in_schema=False)
async def pwg_v2(request: Request, step: int = None, length: int = None, action: str = None):
    generator = RandomPasswordGenerator()
    return templates.TemplateResponse("security/password_generator_v2/home.html",
                                      {"request": request, "password": generator.simple(step=step, length=length),
                                       "length": str(length if length is not None else 6),
                                       "step": str(step if step is not None else 3),
                                       "action": action if action is not None else "hide",
                                       })


@router.get("/home", include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse("home/home.html",
                                      {"request": request})
