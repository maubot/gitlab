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
from functools import partial
from datetime import datetime

from gitlab import Gitlab as Gl

from maubot.handlers import command
from maubot import MessageEvent

from ..util import (OptUrlAliasArgument, OptRepoArgument, with_gitlab_session, sigil_int,
                    optional_int, quote_parser)
from .base import Command


class CommandIssue(Command):
    @Command.gitlab.subcommand("issue", help="Manage GitLab issues.")
    async def issue(self) -> None:
        pass

    @issue.subcommand("close", help="Close an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @OptRepoArgument("repo", "repository")
    @command.argument("id", "issue ID")
    @with_gitlab_session
    async def issue_close(self, evt: MessageEvent, repo: str, id: str, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)
        issue.state_event = "close"
        issue.save()

        await evt.reply(f"Closed issue #{issue.iid}: {issue.title}")

    @issue.subcommand("comment", help="Write a comment on an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=3)
    @OptRepoArgument("repo", "repository")
    @command.argument("id", "issue ID", parser=sigil_int)
    @command.argument("body", "comment body", pass_raw=True)
    @with_gitlab_session
    async def issue_comment(self, evt: MessageEvent, repo: str, id: int, body: str, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)
        issue.notes.create({"body": body.strip()})

        await evt.reply(f"Commented on issue #{issue.iid}: {issue.title}")

    @issue.subcommand("comments", aliases=("read-comments",),
                      help="Write a comment on an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @OptRepoArgument("repo", "repository")
    @command.argument("id", "issue ID", parser=sigil_int)
    @command.argument("page", "page", required=False, parser=optional_int)
    @command.argument("per_page", "entries per page", required=False, parser=optional_int)
    @with_gitlab_session
    async def issue_comments_read(self, evt: MessageEvent, repo: str, id: int,
                                  page: int, per_page: int, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)
        notes = issue.notes.list(per_page=per_page or 5, page=page or 1)

        def format_note(note) -> str:
            body = "\n".join(f"> {line}" for line in note.body.split("\n"))
            date = (datetime
                    .strptime(note.created_at, "%Y-%m-%dT%H:%M:%S.%f%z")
                    .strftime(self.bot.config["time_format"]))
            author = note.author["name"]
            return f"{author} at {date}:\n{body}"

        await evt.reply("\n\n".join(format_note(note) for note in reversed(notes)))

    @issue.subcommand("create", help="Create an Issue. The issue body can be placed on a new line.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=3)
    @OptRepoArgument("repo", "repository")
    @command.argument("title", "issue title", pass_raw=True, parser=quote_parser)
    @command.argument("desc", "issue body", pass_raw=True, required=False,
                      parser=partial(quote_parser, return_all=True))
    @with_gitlab_session
    async def issue_create(self, evt: MessageEvent, repo: str, title: str,
                           desc: str, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.create({"title": title, "description": desc})
        await evt.reply(f"Created issue [#{issue.iid}]({issue.web_url}): {issue.title}")

    @issue.subcommand("read", aliases=("view", "show"),
                      help="Read an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @OptRepoArgument("repo", "repository")
    @command.argument("id", "issue ID", parser=sigil_int)
    @with_gitlab_session
    async def issue_read(self, evt: MessageEvent, repo: str, id: int, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)

        msg = f"Issue #{issue.iid} by {issue.author['name']}: [{issue.title}]({issue.web_url})  \n"
        names = [assignee['name'] for assignee in issue.assignees]
        if len(names) > 1:
            msg += f"Assigned to {', '.join(names[:-1])} and {names[-1]}.  \n"
        elif len(names) == 1:
            msg += f"Assigned to {names[0]}.  \n"
        msg += "\n".join(f"> {line}" for line in issue.description.strip().split("\n"))

        await evt.reply(msg)

    @issue.subcommand("reopen", help="Reopen an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @OptRepoArgument("repo", "repository")
    @command.argument("id", "issue ID", parser=sigil_int)
    @with_gitlab_session
    async def issue_reopen(self, evt: MessageEvent, repo: str, id: int, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)
        issue.state_event = "reopen"
        issue.save()

        await evt.reply(f"Reopened issue #{issue.iid}: {issue.title}")
