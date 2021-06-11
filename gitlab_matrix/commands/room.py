# gitlab - A GitLab client and webhook receiver for maubot
# Copyright (C) 2019 Lorenz Steinert
# Copyright (C) 2021 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from gitlab import Gitlab as Gl, GitlabGetError

from mautrix.types import EventType

from maubot.handlers import command
from maubot import MessageEvent

from ..util import OptUrlAliasArgument, with_gitlab_session
from .base import Command


class CommandRoom(Command):
    @Command.gitlab.subcommand("room", aliases=("r",), help="Manage the settings for this room.")
    async def room(self) -> None:
        pass

    @room.subcommand("default_repo", aliases=("default", "repo", "d", "r"),
                     help="Set the default repo for this room.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @command.argument("repo", "repository")
    @with_gitlab_session
    async def default_repo(self, evt: MessageEvent, repo: str, gl: Gl) -> None:
        power_levels = await self.bot.client.get_state_event(evt.room_id, EventType.ROOM_POWER_LEVELS)
        if power_levels.get_user_level(evt.sender) < power_levels.state_default:
            await evt.reply("You don't have the permission to change the default repo of this room")
            return

        try:
            project = gl.projects.get(repo)
        except GitlabGetError as e:
            if e.response_code == 404:
                await evt.reply(f"Couldn't find {repo} on {gl.url}")
                return
            raise
        self.bot.db.set_default_repo(evt.room_id, gl.url, repo)
        await evt.reply(f"Changed the default repo to {repo} on {gl.url}")
