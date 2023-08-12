from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests
from validator_collection import checkers

from mautrix_iot.configuration import CONF
from mautrix_iot.consts import DEVICE_MESSAGE_FORMAT, HELP_MESSAGE
from mautrix_iot.db.database import Session
from mautrix_iot.db.models import Entity
from mautrix_iot.devices import register_new_device
from mautrix_iot.homeserver_api import create_room, register_user, send_message
from mautrix_iot.utils import bot_full_name, retry_rate_limited


class BasicFlow:
    class BasicState:
        def __init__(self, flow: "BasicFlow", name: str, results: Dict[str, Any], args: List[str]):
            self.name = name
            self.results = results
            self.flow = flow
            self.args = args

        def send_input(self, value: str):
            validated, reason = self.validate(value)
            if not validated:
                return validated, reason

            self.results[self.name] = value

            return True, reason

        def validate(self, value: str):
            return True, None

        @property
        def prompt(self):
            raise NotImplementedError()

    def __init__(self, room_id: str, room_peer: str, args: List[str]):
        self.props: Dict[str, Any] = {}
        self.args = args
        self.states: List[BasicFlow.BasicState] = self.available_states()
        self.state: BasicFlow.BasicState = self.states[0]
        self.room_id = room_id
        self.room_peer = room_peer
        self.done = False

    def available_states(self) -> List[BasicState]:
        return []

    def next_state(self) -> None:
        try:
            index = self.states.index(self.state)
        except ValueError:
            raise ValueError(f"Illegal state: {self.state}")

        if index == len(self.states) - 1:
            self.done_callback()
            return

        self.state = self.states[index + 1]

    @property
    def prompt(self) -> str:
        return self.state.prompt

    def send(self, value: str):
        validated, reason = self.state.send_input(value)

        if validated:
            self.next_state()
            return True, reason

        return validated, reason

    def done_callback(self):
        self.done = True


class HelpFlow(BasicFlow):
    class HelpState(BasicFlow.BasicState):
        @property
        def prompt(self) -> str:
            self.flow.done = True
            return HELP_MESSAGE

    def available_states(self) -> List[BasicFlow.BasicState]:
        return [
            HelpFlow.HelpState(self, "", self.props, self.args),
        ]


class RegisterDeviceFlow(BasicFlow):
    class DeviceNameState(BasicFlow.BasicState):
        def validate(self, value: str):
            if len(value) > 30:
                return False, "❌  Device name too long (max 30 characters)"

            with Session() as db:
                if db.query(Entity).filter(Entity.name == value).first():
                    return False, "❌  Device with the same name already exists"

            return True, None

        @property
        def prompt(self) -> str:
            return "What is the device name?"

    class DeviceHostState(BasicFlow.BasicState):
        def validate(self, value: str):
            if not checkers.is_url(value, allow_special_ips=True):
                return False, "❌  Host is not a valid URL"

            r = requests.get(f"{value}/api/v1/ping")
            if r.status_code != 200:
                return False, "❌  Could not reach device"
            
            r = requests.get(f"{value}/api/v1/commands")
            if r.status_code != 200:
                return False, "❌  Could not fetch available commands"
        
            print(f"--------------HERE----------", r.json(), r.text)
            return True, r.text

        @property
        def prompt(self) -> str:
            return "What is the device host? (e.g. http://192.168.1.5:35329)"

    def available_states(self) -> List[BasicFlow.BasicState]:
        return [
            RegisterDeviceFlow.DeviceNameState(self, "device_name", self.props, self.args),
            RegisterDeviceFlow.DeviceHostState(self, "device_host", self.props, self.args),
        ]

    @retry_rate_limited
    def done_callback(self) -> None:
        super().done_callback()

        register_new_device(self.props, self.room_id, self.room_peer)


class ListDevicesFlow(BasicFlow):
    class ListState(BasicFlow.BasicState):
        @property
        def prompt(self) -> str:
            self.flow.done = True

            with Session() as db:
                devices = db.query(Entity).filter(Entity.is_device == True).all()

                if len(devices) == 0:
                    return "There are no registered devices."
                
                return self._format_devices_list(devices)
            
        def _format_devices_list(self, devices: List[Entity]) -> str:
            message = "<ul> <br> "

            for device in devices:
                message += DEVICE_MESSAGE_FORMAT(device.id, device.name, device.host, device.room_id)
            message += " </ul> "

            return message
        
    def available_states(self) -> List[BasicFlow.BasicState]:
        return [
            ListDevicesFlow.ListState(self, "", self.props, self.args),
        ]

        
class InfoDeviceFlow(BasicFlow):
    class InfoState(BasicFlow.BasicState):
        @property
        def prompt(self) -> str:
            self.flow.done = True

            if len(self.args) != 1:
                return "❌  Provide a registered device name."
            
            device_name = self.args[0]
            
            with Session() as db:
                device = db.query(Entity).filter(Entity.name == device_name).first()

                if device is None:
                    return f"❌ There is no registered device with the name <strong> {device_name} </strong>."
                
                return f"""
                    <ul>
                       <li> <strong> ID: </strong> {device.id} </li>
                       <li> <strong> Name: </strong> {device.name} </li>
                       <li> <strong> Description: </strong> {device.description} </li>
                       <li> <strong> Host: </strong> {device.host} </li>
                       <li> <strong> User: </strong> <a href="https://matrix.to/#/@{device.matrix_id}:{CONF['homeserver']['domain']}"> {device.matrix_id} </a> </li>
                       <li> <strong> Room: </strong> <a href="https://matrix.to/#/{device.room_id}"> {device.room_id} </a> </li>
                       <li> <strong> Access token: </strong> {10 * '*'}{device.access_token[-6:]} </li>
                    </ul>
                """
        
    def available_states(self) -> List[BasicFlow.BasicState]:
        return [
            InfoDeviceFlow.InfoState(self, "", self.props, self.args),
        ]



COMMANDS = {
    "help": HelpFlow,
    "register": RegisterDeviceFlow,
    "list": ListDevicesFlow,
    "info": InfoDeviceFlow,
}
