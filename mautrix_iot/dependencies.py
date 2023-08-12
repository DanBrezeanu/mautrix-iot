from typing import Annotated, Union

from fastapi import Header

from mautrix_iot.configuration import CONF
from mautrix_iot.exceptions import ForbiddenError, UnauthorizedError


async def check_authorization_header(
    authorization: Annotated[Union[str, None], Header()] = None,
):
    if not authorization:
        raise UnauthorizedError()

    if authorization.removeprefix("Bearer ") != CONF.appservice["hs_token"]:
        raise ForbiddenError()
