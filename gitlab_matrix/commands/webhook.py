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
import secrets

from gitlab import Gitlab as Gl

from maubot import MessageEvent

from ..util import OptUrlAliasArgument, OptRepoArgument, with_gitlab_session
from .base import Command


class CommandWebhook(Command):
    @Command.gitlab.subcommand("webhook", help="Manage GitLab webhooks.")
    async def webhook(self) -> None:
        pass

    @webhook.subcommand("add", help="Add a webhook to post updates to this room")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=1)
    @OptRepoArgument("repo", "repository")
    @with_gitlab_session
    async def webhook_add(self, evt: MessageEvent, repo: str, gl: Gl) -> None:
        token = secrets.token_urlsafe(64)
        await self.bot.db.add_webhook_room(token, evt.room_id)
        project = gl.projects.get(repo)
        hook = project.hooks.create({
            "url": f"{self.bot.webapp_url}/webhooks",
            "push_events": True,
            "tag_push_events": True,
            "issues_events": True,
            "merge_requests_events": True,
            "note_events": True,
            "job_events": True,
            "token": token,
        })
        await evt.reply(f"Added [**webhook #{hook.id}**]({project.web_url}/-/hooks/{hook.id}/edit)"
                        f" for {project.path_with_namespace}")
