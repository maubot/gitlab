# gitlab - A GitLab client and webhook receiver for maubot
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
from typing import TYPE_CHECKING

from maubot.handlers import command

if TYPE_CHECKING:
    from ..bot import GitlabBot


class Command:
    bot: 'GitlabBot'

    def __init__(self, bot: 'GitlabBot') -> None:
        self.bot = bot

    @command.new(name="gitlab", help="Manage this Gitlab bot",
                 require_subcommand=True)
    async def gitlab(self) -> None:
        pass
