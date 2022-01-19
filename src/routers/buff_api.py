from fastapi import APIRouter, Depends
from fastapi_jwt_auth import AuthJWT

from src.models.buff_model import BuffSettings, RegisterFarmForm


@AuthJWT.load_config
def get_config():
    return BuffSettings()


router = APIRouter()


@router.get("/", include_in_schema=False)
async def main():
    return "Buff management is connected"


@router.post("/register", include_in_schema=True)
async def register(farm: RegisterFarmForm = Depends(RegisterFarmForm.as_form), Authorize: AuthJWT = Depends()):

    return "REGISTER"
