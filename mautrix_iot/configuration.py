from typing import Any, Dict

import yaml


class Configuration:
    def __init__(self):
        self.conf = self.read_configuration("bridge.yaml")

    def read_configuration(self, filename: str) -> Dict[str, Any]:
        with open(filename, "r") as f:
            return yaml.full_load(f)

    def __getitem__(self, key: str) -> Any:
        return self.conf[key]

    def __getattr__(self, name: str) -> Any:
        return self.conf[name]


CONF = Configuration()
