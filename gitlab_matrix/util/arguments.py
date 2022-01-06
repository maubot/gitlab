# gitlab - A GitLab client and webhook receiver for maubot
# Copyright (C) 2019 Lorenz Steinert
# Copyright (C) 2019 Tulir Asokan
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
from typing import Tuple, Any, Optional, TYPE_CHECKING
import re

from maubot import MessageEvent
from maubot.handlers.command import Argument

if TYPE_CHECKING:
    from ..commands import Command


class OptUrlAliasArgument(Argument):
    def __init__(self, name: str, label: str = None,
                 arg_num: int = 1, *, required: bool = False):
        super().__init__(name, label=label, required=required, pass_raw=True)
        self.arg_num = arg_num

    def match(self, val: str, evt: MessageEvent, instance: 'Command', **kwargs
              ) -> Tuple[str, Any]:
        vals = val.split(" ")

        if (len(vals) > self.arg_num
                and (vals[0] in instance.bot.db.get_servers(evt.sender)
                     or vals[0] in instance.bot.db.get_aliases(evt.sender))):
            return " ".join(vals[1:]), instance.bot.db.get_login(evt.sender, url_alias=vals[0])
        return val, instance.bot.db.get_login(evt.sender)


class OptRepoArgument(Argument):
    def __init__(self, name: str, label: str = None, required: bool = False) -> None:
        super().__init__(name, label=label, required=required)

    def match(self, val: str, evt: MessageEvent, instance: 'Command', **kwargs
              ) -> Tuple[str, Any]:
        repo = re.split(r"\s", val, 1)[0]

        default_repo = instance.bot.db.get_default_repo(evt.room_id)
        if not default_repo or re.fullmatch(r"\w+/[\w/]+", repo):
            return val[len(repo):], repo
        return val, default_repo


def optional_int(val: str) -> Optional[int]:
    if not val:
        return None
    return int(val)


def quote_parser(val: str, return_all: bool = False) -> Tuple[str, Optional[str]]:
    if len(val) == 0:
        return val, None

    if val[0] in ('"', "'"):
        try:
            next_quote = val.index(val[0], 1)
            return val[next_quote + 1:], val[1:next_quote]
        except ValueError:
            pass
    if return_all:
        return "", val
    vals = val.split("\n", 1)
    if len(vals) == 1:
        return "", vals[0]
    else:
        return vals[1], vals[0]


def sigil_int(val: str) -> int:
    if len(val) == 0:
        raise ValueError('No issue ID given')
    if val[0] == '#':
        return int(val[1:])
    return int(val)
