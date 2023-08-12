from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

import requests

from mautrix_iot.configuration import CONF
from mautrix_iot.exceptions import RateLimitedError


def _make_request(
    endpoint: str,
    method: Literal["get", "head", "post", "put", "patch", "delete"],
    payload: Optional[Dict[str, Any]] = None,
    version: str = "v3",
    access_token: Optional[str] = None,
) -> requests.Response:
    response = getattr(requests, method)(
        f"{CONF.homeserver['address']}/_matrix/client/{version}/{endpoint}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token or CONF.appservice['as_token']}",
        },
        json=payload or {},
    )

    if response.status_code == 429:
        raise RateLimitedError()

    return response


def send_message(
    body: str,
    room_id: str,
    sender: str,
    formatted_body: Optional[str] = None,
    **kwargs,
) -> Tuple[int, Dict[str, Any]]:
    formatted_params = {}
    if formatted_body is not None:
        formatted_params = {
            "format": "org.matrix.custom.html",
            "formatted_body": formatted_body,
        }

    response = _make_request(
        endpoint=f"rooms/{room_id}/send/m.room.message/{uuid4()}",
        method="put",
        payload={
            "msgtype": "m.text",
            "body": body,
            **formatted_params,
        },
        **kwargs,
    )

    print(response)

    return (response.status_code, response.json())


def create_room(name: str, room_peer: str, is_direct: bool = True, **kwargs):
    response = _make_request(
        endpoint="createRoom",
        method="post",
        payload={
            "invite": [room_peer],
            "name": name,
            "preset": "private_chat",
            "is_direct": is_direct,
        },
        **kwargs,
    )

    return (response.status_code, response.json())


def register_user(username: str, **kwargs) -> Tuple[int, Dict[str, Any]]:
    response = _make_request(
        endpoint="register",
        method="post",
        payload={
            "type": "m.login.application_service",
            "username": username,
        },
        **kwargs,
    )

    return (response.status_code, response.json())


def join_room(room_id: str, **kwargs) -> Tuple[int, Dict[str, Any]]:
    response = _make_request(
        f"rooms/{room_id}/join",
        "post",
        **kwargs,
    )

    return (response.status_code, response.json())


def leave_room(room_id: str, **kwargs) -> Tuple[int, Dict[str, Any]]:
    response = _make_request(
        f"rooms/{room_id}/leave",
        "post",
        **kwargs,
    )

    return (response.status_code, response.json())
