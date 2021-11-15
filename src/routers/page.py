from fastapi import APIRouter, Request

from src.environment.share_environment import templates
from src.tools.random_password_generator import RandomPasswordGenerator, SimpleRPWGModel

router = APIRouter()


@router.get("/pwg", include_in_schema=True)
async def pwg(request: Request, step: int = None):
    generator = RandomPasswordGenerator()
    password = generator.simple(step=step) if step is not None else generator.simple()
    return templates.TemplateResponse("security/password_generator/home.html",
                                      {"request": request, "password": password})
