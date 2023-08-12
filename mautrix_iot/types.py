from typing import Any, Dict, List, TypedDict


class _DeviceAPIResponseError(TypedDict):
    code: str
    message: str


class DeviceAPIResponse(TypedDict):
    error: _DeviceAPIResponseError
    response: Dict[str, Any]


class _DeviceAPIResponseCommand(TypedDict):
    name: str
    alias: str
    description: str
    args: List[str]


class DeviceAPIResponseCommands(DeviceAPIResponse):
    response: List[_DeviceAPIResponseCommand]


class DeviceAPIResponseSendCommand(DeviceAPIResponse):
    response: str
