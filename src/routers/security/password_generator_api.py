from fastapi import APIRouter, Depends

from src.models.random_password_model import SimpleRandomPasswordModel, RandomPasswordModel
from src.tools.generators.random_password_generator import RandomPasswordGenerator

router = APIRouter()
generator = RandomPasswordGenerator()


@router.get("/simple")
async def simple(model: SimpleRandomPasswordModel = Depends()):
    if model.step is None or model.length is None:
        return generator.simple()
    else:
        return generator.advance(step=model.step,
                                 length=model.length)


@router.post("/custom")
async def custom(req: RandomPasswordModel):
    return generator.custom(req)
