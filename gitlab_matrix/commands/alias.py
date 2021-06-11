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
from maubot.handlers import command
from maubot import MessageEvent

from .base import Command


class CommandAlias(Command):
    @Command.gitlab.subcommand("alias", aliases=("a",), help="Manage Gitlab server aliases.")
    async def alias(self) -> None:
        pass

    @alias.subcommand("add", aliases=("a",), help="Add a alias to a GitLab server.")
    @command.argument("url", "server URL")
    @command.argument("alias", "server alias")
    async def alias_add(self, evt: MessageEvent, url: str, alias: str) -> None:
        if url not in self.bot.db.get_servers(evt.sender):
            await evt.reply("You can't add an alias to a GitLab server you are not logged in to.")
            return
        if self.bot.db.has_alias(evt.sender, alias):
            await evt.reply("Alias already in use.")
            return
        self.bot.db.add_alias(evt.sender, url, alias)
        await evt.reply(f"Added alias {alias} to server {url}")

    @alias.subcommand("list", aliases=("l", "ls"), help="Show your Gitlab server aliases.")
    async def alias_list(self, evt: MessageEvent) -> None:
        aliases = self.bot.db.get_aliases(evt.sender)
        if not aliases:
            await evt.reply("You don't have any aliases.")
            return
        msg = ("You have the following aliases:\n\n"
               + "\n".join(f"+ {alias.alias} → {alias.server}" for alias in aliases))
        await evt.reply(msg)

    @alias.subcommand("remove", aliases=("r", "rm", "d", "del", "delete"),
                      help="Remove a alias to a Gitlab server.")
    @command.argument("alias", "server alias")
    async def alias_rm(self, evt: MessageEvent, alias: str) -> None:
        self.bot.db.rm_alias(evt.sender, alias)
        await evt.reply(f"Removed alias {alias}.")
