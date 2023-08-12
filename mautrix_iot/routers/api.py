from typing import Annotated, Optional, Union

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from mautrix_iot.dependencies import check_authorization_header
from mautrix_iot.matrix import EventHandler

router = APIRouter(
    prefix="/_matrix/app/v1", dependencies=[Depends(check_authorization_header)]
)
event_handler = EventHandler()


@router.post(f"/ping")
async def ping():
    return JSONResponse({})


@router.put("/transactions/{txd}")
async def ping(
    body: dict,
    txd: str,
    authorization: Annotated[Union[str, None], Header()] = None,
):
    print(txd)
    print(authorization)
    print(body)

    event_handler.determine_and_handle_event(body)

    return JSONResponse({})
