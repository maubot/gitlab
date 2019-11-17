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
from typing import Tuple, Any, Optional, Callable, TYPE_CHECKING
import re

from gitlab import Gitlab as Gl
from gitlab.exceptions import GitlabAuthenticationError

from maubot import MessageEvent
from maubot.handlers.command import Argument

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from .db import AuthInfo, DefaultRepoInfo

if TYPE_CHECKING:
    from .bot import GitlabBot


class OptUrlAliasArgument(Argument):
    def __init__(self, name: str, label: str = None,
                 arg_num: int = 1, *, required: bool = False):
        super().__init__(name, label=label, required=required, pass_raw=True)
        self.arg_num = arg_num

    def match(self, val: str, evt: MessageEvent, instance: 'GitlabBot', **kwargs
              ) -> Tuple[str, Any]:
        vals = val.split(" ")

        if (len(vals) > self.arg_num
                and (vals[0] in instance.db.get_servers(evt.sender)
                     or vals[0] in instance.db.get_aliases(evt.sender))):
            return " ".join(vals[1:]), instance.db.get_login(evt.sender, url_alias=val[0])
        return val, instance.db.get_login(evt.sender)


class OptRepoArgument(Argument):
    def __init__(self, name: str, label: str = None, required: bool = False) -> None:
        super().__init__(name, label=label, required=required)

    def match(self, val: str, evt: MessageEvent, instance: 'GitlabBot', **kwargs
              ) -> Tuple[str, Any]:
        repo = re.split(r"\s", val, 1)[0]

        default_repo = instance.db.get_default_repo(evt.room_id)
        if not default_repo or re.fullmatch(r"\w+/[\w/]+", repo):
            return val[len(repo):], repo
        return val, default_repo


Decoratable = Callable[['GitlabBot', MessageEvent, Gl, Any], Any]
Decorator = Callable[['GitlabBot', MessageEvent, AuthInfo, Any], Any]


def with_gitlab_session(func: Decoratable) -> Decorator:
    async def wrapper(self, evt: MessageEvent, login: AuthInfo, **kwargs) -> Any:
        try:
            repo = kwargs["repo"]
            if isinstance(repo, DefaultRepoInfo):
                if repo.server not in self.db.get_servers(evt.sender):
                    await evt.reply(f"You're not logged into {repo.server}")
                    return
                login = self.db.get_login(evt.sender, url_alias=repo.server)
                kwargs["repo"] = repo.repo
        except KeyError:
            pass

        try:
            with Gl(login.server, login.api_token) as gl:
                return await func(self, evt, gl=gl, **kwargs)
        except GitlabAuthenticationError as e:
            await evt.reply("Invalid access token.\n\n{0}".format(e))
        except Exception:
            self.log.error("Failed to handle command", exc_info=True)

    return wrapper


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("path")
        helper.copy("secret")
        helper.copy("base_command")
        helper.copy("send_as_notice")
        helper.copy("time_format")


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
