from fastapi import APIRouter

router = APIRouter()


@router.get("/users/", tags=["users"],include_in_schema=False)
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.get("/users/me", tags=["users"],include_in_schema=False)
async def read_user_me():
    return {"username": "fakecurrentuser"}


@router.get("/users/{username}", tags=["users"],include_in_schema=False)
async def read_user(username: str):
    return {"username": username}