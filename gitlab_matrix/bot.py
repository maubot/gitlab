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
from typing import Type

from mautrix.util.config import BaseProxyConfig
from maubot import Plugin

from .db import Database
from .util import Config
from .webhook import GitlabWebhook
from .commands import GitlabCommands


class GitlabBot(Plugin):
    db: Database
    webhook: GitlabWebhook
    commands: GitlabCommands

    async def start(self) -> None:
        self.config.load_and_update()

        self.db = Database(self.database)
        self.webhook = await GitlabWebhook(self).start()
        self.commands = GitlabCommands(self)

        self.register_handler_class(self.webhook)
        self.register_handler_class(self.commands)

    async def stop(self) -> None:
        await self.webhook.stop()

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
