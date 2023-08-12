import time
from functools import reduce
from typing import List

from mautrix_iot.configuration import CONF
from mautrix_iot.exceptions import RateLimitedError
from mautrix_iot.types import _DeviceAPIResponseCommand


def retry_rate_limited(func):
    def wrapper(*args, **kwargs):
        retries = 1

        while retries <= CONF.appservice["rate_limit_retry"]:
            try:
                func(*args, **kwargs)
            except RateLimitedError:
                retries += 1
                time.sleep(1)
            else:
                break

    return wrapper


def bot_full_name() -> str:
    return f"@{CONF.appservice['bot_username']}:{CONF.homeserver['domain']}"


def format_commands(commands: List[_DeviceAPIResponseCommand]) -> str:
    return reduce(
        lambda a, b: a + b,
        [
            f"""    
<strong> {command['name']} </strong> \
{" ".join([f'<em>&lt;{arg}&gt;</em>' for arg in command['args']])} - 
{command['description']} <br>
"""
            for command in commands
        ],
    )


def format_body_for_room():
    pass
