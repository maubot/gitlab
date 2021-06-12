from .base import Command
from .room import CommandRoom
from .issue import CommandIssue
from .alias import CommandAlias
from .server import CommandServer
from .commit import CommandCommit
from .webhook import CommandWebhook


class GitlabCommands(CommandRoom, CommandIssue, CommandAlias, CommandServer, CommandCommit,
                     CommandWebhook):
    pass


__all__ = ["GitlabCommands", "Command"]
