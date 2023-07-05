from datadog_checks.checks import AgentCheck
from datadog_checks.base.utils import subprocess_output
from datadog_checks.base.types import ServiceCheck
from dataclasses import dataclass
from typing import List


@dataclass
class LaunchdService:
    pid: str
    status: str
    label: str


class LaunchdListing:
    services: List[LaunchdService]

    def __init__(self):
        output = subprocess_output.get_subprocess_output(
            ["launchctl", "list"], raise_on_empty_output=True
        )
        self.services = [
            LaunchdService(row[0], row[1], row[2])
            for row in list(
                map(lambda x: x.split("\t"), output.decode().splitlines()[1:])
            )
        ]

    def is_running(self, label: str) -> bool:
        if not self.is_loaded(label):
            return False

        entry = list(filter(lambda x: x.label == label, self.services))[0]
        return entry.pid != "-"

    def is_loaded(self, label: str) -> bool:
        listing = list(filter(lambda x: x.label == label, self.services))
        return len(listing) > 0


class LaunchdServiceCheck(AgentCheck):
    def check(self, instance):
        try:
            launchd = LaunchdListing()
        except Exception:
            self.service_check(instance["name"], ServiceCheck.UNKNOWN)
            return

        if launchd.is_running(instance["label"]):
            self.service_check(instance["name"], ServiceCheck.OK)
        else:
            self.service_check(instance["name"], ServiceCheck.CRITICAL)
