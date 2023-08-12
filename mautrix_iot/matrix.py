from typing import Any, Dict

import requests

from mautrix_iot.configuration import CONF
from mautrix_iot.consts import (
    BRIDGE_USERS_PREFIX,
    HELP_MESSAGE,
    UNKNOWN_COMMAND_MESSAGE,
    MatrixEventType,
)
from mautrix_iot.db.database import get_bot_entity, get_entity_for_room
from mautrix_iot.db.models import Entity
from mautrix_iot.db.operations import delete_bot_room, get_bot_entity, update_bot_room
from mautrix_iot.device_api import get_available_device_commands, send_command
from mautrix_iot.exceptions import BadJsonError
from mautrix_iot.flows import COMMANDS, BasicFlow
from mautrix_iot.homeserver_api import create_room, join_room, leave_room, send_message
from mautrix_iot.utils import bot_full_name, format_commands, retry_rate_limited


class EventHandler:
    def __init__(self):
        self.flow: BasicFlow = None

    def determine_and_handle_event(self, request):
        events = request.get("events", [])
        if len(events) == 0:
            return

        latest_event = events[0]

        if "type" not in latest_event:
            return

        if latest_event["type"] == MatrixEventType.ROOM.value:
            if latest_event.get("content", {}).get("membership") == "invite":
                self._handle_bot_invite(latest_event)
            elif latest_event.get("content", {}).get("membership") == "leave":
                self._handle_room_leave(latest_event)

        elif latest_event["type"] == MatrixEventType.MESSAGE.value:
            self._handle_message(latest_event)

    @retry_rate_limited
    def _handle_message(self, event):
        if "room_id" not in event:
            raise BadJsonError()

        # Ignore if bot sent the message
        if event.get("sender", "").startswith(BRIDGE_USERS_PREFIX):
            return

        room_id = event["room_id"]

        device = get_entity_for_room(room_id)

        # No bot registered with this room
        if device is None:
            # Try to see if management bot is invited
            status_code, _ = join_room(room_id)

            # If this succeeded, then this is the new management room
            if status_code == 200:
                update_bot_room(room_id, bot_full_name())
                device = get_bot_entity()
            # Do not know with whom to respond, abort
            else:
                return

        # Management command
        if not device.is_device:
            self._handle_message_with_bot(event, device, room_id)
        else:
            self._handle_message_with_device(event, device, room_id)

    @retry_rate_limited
    def _handle_message_with_bot(
        self, event: Dict[str, Any], bot: Entity, room_id: str
    ):
        message = event["content"]["body"]
        command, *args = message.split()

        if command in COMMANDS:
            self.flow = COMMANDS[command](room_id, event["sender"], args)
            send_message(
                body=self.flow.prompt,
                formatted_body=self.flow.prompt,
                room_id=room_id,
                sender=bot.matrix_id,
            )
        elif self.flow and not self.flow.done:
            validated, reason = self.flow.send(message)
            print(reason)

            if reason:
                send_message(
                    body=reason,
                    formatted_body=reason,
                    room_id=room_id,
                    sender=bot.matrix_id,
                )

            if not self.flow.done:
                send_message(
                    body=self.flow.prompt,
                    formatted_body=self.flow.prompt,
                    room_id=room_id,
                    sender=bot.matrix_id,
                )
        else:
            send_message(
                UNKNOWN_COMMAND_MESSAGE,
                formatted_body=UNKNOWN_COMMAND_MESSAGE,
                room_id=room_id,
                sender=bot.matrix_id,
            )

    @retry_rate_limited
    def _handle_message_with_device(
        self, event: Dict[str, Any], device: Entity, room_id: str
    ):
        response = get_available_device_commands(device)

        if response["error"]["code"] != "OK":
            send_message(
                body="Could not retrieve commands from device.",
                formatted_body="Could not retrieve commands from device.",
                room_id=room_id,
                sender=device.matrix_id,
                access_token=device.access_token,
            )
            return

        message = event["content"]["body"]
        command, *args = message.split()
        available_commands = response["response"]

        if command == "help":
            send_message(
                body=format_commands(available_commands),
                formatted_body=format_commands(available_commands),
                room_id=room_id,
                sender=device.matrix_id,
                access_token=device.access_token,
            )

        elif command in (comm["name"] for comm in available_commands):
            # self.flow = COMMANDS[command](room_id, event["sender"], args)
            response = send_command(device, command, args)

            if response["error"]["code"] != "OK":
                body = response["error"]["message"]
            else:
                body = response["response"]

            send_message(
                body=body,
                formatted_body=body,
                room_id=room_id,
                sender=device.matrix_id,
                access_token=device.access_token,
            )
        else:
            send_message(
                UNKNOWN_COMMAND_MESSAGE,
                formatted_body=UNKNOWN_COMMAND_MESSAGE,
                room_id=room_id,
                sender=device.matrix_id,
                access_token=device.access_token,
            )

    @retry_rate_limited
    def _handle_bot_invite(self, event):
        if "room_id" not in event:
            raise BadJsonError()

        room_id = event["room_id"]

        if event.get("state_key", "") != bot_full_name():
            return

        status_code, _ = join_room(room_id)

        # Not allowed to join, log this
        if status_code == 403:
            pass

        bot = get_bot_entity()
        if bot.room:
            if bot.room.id != room_id:
                send_message(
                    "You already have private chat portal at "
                    f"https://matrix.to/#/{bot.room.id}:{CONF.homeserver['domain']}",
                    formatted_body=(
                        "You already have private chat portal at "
                        f'<a href="https://matrix.to/#/{bot.room.id}">'
                        f"{bot.room.id}</a>"
                    ),
                    room_id=room_id,
                    sender=bot_full_name(),
                )
                leave_room(room_id)
        else:
            update_bot_room(room_id, bot_full_name())

    @retry_rate_limited
    def _handle_room_leave(self, event):
        if "room_id" not in event:
            raise BadJsonError()

        # Bot left, do nothing
        if event.get("user_id", "") == bot_full_name():
            return

        status_code, _ = leave_room(event["room_id"])

        delete_bot_room()
