import discord
from lib.date_tools import time_ago
from functools import cached_property

class BotResponse:
    def __init__(self, response: str, is_error: bool = False):
        self.start = discord.utils.utcnow()
        self.response = response
        self.is_error = is_error

    @cached_property
    def timestamp(self):
        return time_ago(self.start)
    @cached_property
    def text(self):
        return f"Duck({self.timestamp}): {self.response}" 
    def __str__(self):
        return f"Response: {self.response}, Is Error: {self.is_error}"
