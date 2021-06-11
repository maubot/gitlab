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
from gitlab import Gitlab as Gl, GitlabAuthenticationError

from maubot.handlers import command
from maubot import MessageEvent

from ..util import OptUrlAliasArgument, with_gitlab_session
from .base import Command


class CommandServer(Command):
    @Command.gitlab.subcommand("server", aliases=("s",), help="Manage GitLab Servers.")
    async def server(self) -> None:
        pass

    @server.subcommand("default", aliases=("d",), help="Change your default GitLab server.")
    @command.argument("url", "server URL")
    async def server_default(self, evt: MessageEvent, url: str) -> None:
        self.bot.db.change_default(evt.sender, url)
        await evt.reply(f"Changed the default server to {url}")

    @server.subcommand("list", aliases=("ls",), help="Show your GitLab servers.")
    async def server_list(self, evt: MessageEvent) -> None:
        servers = self.bot.db.get_servers(evt.sender)
        if not servers:
            await evt.reply("You are not logged in to any server.")
            return
        await evt.reply("You are logged in to the following servers:\n\n"
                        + "\n".join(f"* {server}" for server in servers))

    @server.subcommand("login", aliases=("l",),
                       help="Add a Gitlab access token for a Gitlab server.")
    @command.argument("url", "server URL")
    @command.argument("token", "access token", pass_raw=True)
    async def server_login(self, evt: MessageEvent, url: str, token: str) -> None:
        gl = Gl(url, private_token=token)
        try:
            gl.auth()
        except GitlabAuthenticationError:
            await evt.reply("Invalid access token")
            return
        except Exception as e:
            self.bot.log.warning(f"Unexpected error logging into GitLab {url} for {evt.sender}",
                             exc_info=True)
            await evt.reply(f"GitLab login failed: {e}")
            return
        self.bot.db.add_login(evt.sender, url, token)
        await evt.reply(f"Successfully logged into GitLab at {url} as {gl.user.name}")

    @server.subcommand("logout", help="Remove the access token from the bot's database.")
    @command.argument("url", "server URL")
    async def server_logout(self, evt: MessageEvent, url: str) -> None:
        self.bot.db.rm_login(evt.sender, url)
        await evt.reply(f"Removed {url} from the database.")

    @Command.gitlab.subcommand("ping", aliases=("p",), help="Ping the bot.")
    async def ping(self, evt: MessageEvent) -> None:
        await evt.reply("Pong")

    @Command.gitlab.subcommand("whoami", help="Check who you're logged in as.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=0)
    @with_gitlab_session
    async def whoami(self, evt: MessageEvent, gl: Gl) -> None:
        gl.auth()
        await evt.reply(f"You're logged into {URL(gl.url).host} as "
                        f"[{gl.user.name}]({gl.url}/{gl.user.username})")
