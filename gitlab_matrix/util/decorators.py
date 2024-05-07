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
from typing import Any, Callable, TYPE_CHECKING

from gitlab import Gitlab as Gl
from gitlab.exceptions import GitlabAuthenticationError

from maubot import MessageEvent

from ..db import AuthInfo, DefaultRepoInfo

if TYPE_CHECKING:
    from ..commands import Command


Decoratable = Callable[['Command', MessageEvent, Gl, Any], Any]
Decorator = Callable[['Command', MessageEvent, AuthInfo, Any], Any]


def with_gitlab_session(func: Decoratable) -> Decorator:
    async def wrapper(self: 'Command', evt: MessageEvent, login: AuthInfo, **kwargs
                      ) -> Any:
        try:
            repo: Any = kwargs["repo"]
            if isinstance(repo, DefaultRepoInfo):
                servers = await self.bot.db.get_servers(evt.sender)
                if repo.server not in servers:
                    await evt.reply(f"You're not logged into {repo.server}")
                    return
                login = await self.bot.db.get_login(evt.sender, url_alias=repo.server)
                kwargs["repo"] = repo.repo
        except KeyError:
            pass

        try:
            with Gl(login.server, login.api_token) as gl:
                return await func(self, evt, gl=gl, **kwargs)
        except GitlabAuthenticationError as e:
            await evt.reply(f"Invalid access token.\n\n{e}")
        except Exception:
            self.bot.log.error("Failed to handle command", exc_info=True)

    return wrapper

