from fastapi import APIRouter, Request, Response
from fastapi_microsoft_identity import initialize, requires_auth, AuthError, validate_scope

router = APIRouter()

initialize(
    tenant_id_='462a1bf3-b70d-499b-9d53-c04ee53b5ba5',
    client_id_='3f7f89d0-baa6-418c-93f9-33bbc8e482f5'
)
expected_scope = "data.read"


# expected_scope = "Files.ReadWrite.All"

@router.get("/", include_in_schema=False)
async def main():
    return "Azure is connected"


@router.get("/test", include_in_schema=False)
@requires_auth
async def test(req: Request):
    try:
        validate_scope(expected_scope, req)
    except AuthError as e:
        print(e.status_code)
        print(e.error_msg)
        return Response(content=e.error_msg, status_code=e.status_code)
    return {
        "HELLO"
    }


@router.get("/oauth/callback", include_in_schema=False)
async def callback():
    return "Callback is called"
