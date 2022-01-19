from fastapi import APIRouter

router = APIRouter()


@router.get("/", include_in_schema=False)
async def main():
    return "Buff management is connected"



