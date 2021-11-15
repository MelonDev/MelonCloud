from fastapi import APIRouter

from src.tools import random_password_generator
from src.tools.random_password_generator import RandomPasswordGenerator

router = APIRouter()

generator = RandomPasswordGenerator()


@router.get("/simple", include_in_schema=True)
async def simple_password():
    return generator.simple()
