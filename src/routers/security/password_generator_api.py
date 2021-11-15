from fastapi import APIRouter, Depends

from src.tools.random_password_generator import RandomPasswordGenerator, SimpleRPWGModel, RPWGModel

router = APIRouter()
generator = RandomPasswordGenerator()


@router.get("/simple")
async def simple(model: SimpleRPWGModel = Depends()):
    if model.step is None or model.length is None:
        return generator.simple()
    else:
        return generator.advance(step=model.step,
                                 length=model.length)


@router.post("/custom")
async def custom(req: RPWGModel):
    return generator.custom(req)
