import enum

AS_TOKEN = "O2tPjGaCj2V9BtvRHybMhU6NzCmnqpLxWyJ7T9vLNTZVbK2I5MYiJ4BPT-ZwwmRm"
HS_TOKEN = "4aRzTJkTQutb9QrfbPVEjlFlRhrIr10t_OswuI95s1RQyDOSNwP7pGHtAnoWGtHM"

MAX_RETRIES = 5


class MatrixErrorCode(enum.Enum):
    M_FORBIDDEN = 403
    M_UNKNOWN_TOKEN = 403
    M_MISSING_TOKEN = 401
    M_BAD_JSON = 400
    M_NOT_JSON = 400
    M_NOT_FOUND = 404
    M_LIMIT_EXCEEDED = 429
    M_UNRECOGNIZED = 405
    M_UNKNOWN = 400
    M_INVALID_USERNAME = 400


class MatrixEventType(enum.Enum):
    ROOM = "m.room.member"
    MESSAGE = "m.room.message"


HELP_MESSAGE = """
<p>This is your management room:</p>
<h4>General</h4>
<strong>help</strong> - Show this help message<br>
<strong>cancel</strong> - Cancel running command<br>
<h4>Devices</h4>
<strong>register</strong> - Register new IoT device<br>
<strong>list</strong> - List registered devices<br>
<strong>info</strong> <em>&lt;name&gt;</em> - Details about a device<br>
"""

DEVICE_MESSAGE_FORMAT = lambda id, name, host, room_id: f"""
 <li> {name}
 <ul>
 <li> <strong> Host: </strong> {host} </li>
 <li> <strong> Room: </strong> <a href="https://matrix.to/#/{room_id}"> {room_id} </a> </li>
 </ul>
 </li>
 <br> 
"""

UNKNOWN_COMMAND_MESSAGE = (
    "This is not a registered command. Send <strong>help</strong> "
    "for the available commands."
)


BRIDGE_USERS_PREFIX = "@iot_"
