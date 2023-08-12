from typing import Any, Dict
from uuid import uuid4

from mautrix_iot.configuration import CONF
from mautrix_iot.db.database import Session
from mautrix_iot.db.models import Entity, Room
from mautrix_iot.homeserver_api import create_room, register_user, send_message
from mautrix_iot.utils import bot_full_name


def register_new_device(data: Dict[str, Any], bot_room_id: str, room_peer_id: str):
    device_matrix_username = f"iot_{uuid4()}"
    status_code, response = register_user(username=device_matrix_username)

    if status_code != 200:
        if status_code == 400 or status_code == 403:
            message = f"❌  Unable to setup device: ({status_code}) {response.get('error', '')}"
        elif status_code == 401:
            message = (
                f"❌  Unable to setup device: ({status_code}) Required more authentication information",
            )
        else:
            message = f"❌  Unable to setup device"

        send_message(
            message,
            room_id=bot_room_id,
            sender=bot_full_name(),
        )
        return

    with Session() as db:
        db.add(
            Entity(
                name=data["device_name"],
                host=data["device_host"],
                matrix_id=device_matrix_username,
                access_token=response["access_token"],
                is_device=True,
            )
        )

    send_message(
        f"Registered user {response['user_id']}",
        room_id=bot_room_id,
        sender=bot_full_name(),
    )

    status_code, response = create_room(
        name=data["device_name"],
        room_peer=room_peer_id,
        access_token=response["access_token"],
    )

    if status_code == 400:
        send_message(
            f"❌ Could not create room with new device: {response['error']}",
            room_id=bot_room_id,
            sender=bot_full_name(),
        )
        return

    direct_room_id = response["room_id"]

    with Session() as db:
        db.add(
            Room(
                id=direct_room_id,
                entity=db.query(Entity)
                .filter(Entity.name == data["device_name"])
                .first(),
                user_matrix_id=room_peer_id,
            )
        )

    send_message(
        body=f"You can start chatting with the device at https://matrix.to/#/{direct_room_id}:{CONF.homeserver['domain']}",
        formatted_body=(
            "You can start chatting with the device at "
            f'<a href="https://matrix.to/#/{direct_room_id}">'
            f"{direct_room_id}</a>"
        ),
        room_id=bot_room_id,
        sender=bot_full_name(),
    )
