from typing import Any, Dict, List

import requests

from mautrix_iot.db.models import Entity
from mautrix_iot.types import DeviceAPIResponseCommands, DeviceAPIResponseSendCommand


def get_available_device_commands(device: Entity) -> DeviceAPIResponseCommands:
    try:
        response = requests.get(f"{device.host}/api/v1/commands")
    except requests.exceptions.ConnectionError as error:
        return {"error": {"code": "CONN_ERR", "message": str(error)}, "response": []}

    print(response.json())
    return {"error": {"code": "OK", "message": ""}, "response": response.json()}


def send_command(
    device: Entity, command: str, args: List[str]
) -> DeviceAPIResponseSendCommand:
    try:
        response = requests.post(
            f"{device.host}/api/v1/command",
            json={
                "command": command,
                "args": args,
            },
        )
    except requests.exceptions.ConnectionError as error:
        return {"error": {"code": "CONN_ERR", "message": str(error)}, "response": {}}

    if response.status_code != 200:
        return {
            "error": {"code": response.status_code, "message": response.text},
            "response": {},
        }

    return {"error": {"code": "OK", "message": ""}, "response": response.text}
