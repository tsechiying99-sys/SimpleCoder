"""A tools that tells the agent the current time."""

import time
from .base import Tool


class NowTool(Tool):
    name = "now"
    description = "Get the current local date and time. Use this when the user asks about the current time or you need a timestamp."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def execute(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")