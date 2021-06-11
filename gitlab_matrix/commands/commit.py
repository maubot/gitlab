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
from datetime import datetime
import re

from gitlab import Gitlab as Gl

from maubot.handlers import command
from maubot import MessageEvent

from ..util import OptUrlAliasArgument, OptRepoArgument, with_gitlab_session, optional_int
from .base import Command


class CommandCommit(Command):
    @Command.gitlab.subcommand("commit", help="View GitLab commits.")
    async def commit(self) -> None:
        pass

    @commit.subcommand("diff", help="Get the diff of a specific commit.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @OptRepoArgument("repo", "repository")
    @command.argument("hash", "commit hash")
    @with_gitlab_session
    async def diff(self, evt: MessageEvent, repo: str, hash: str, gl: Gl) -> None:
        project = gl.projects.get(repo)
        diffs = project.commits.get(hash).diff()

        def color_diff(line: str) -> str:
            if line.startswith("@@") and re.fullmatch(r"(@@ -[0-9]+,[0-9]+ \+[0-9]+,[0-9]+ @@)",
                                                      line):
                return f"<font color='#00A'>{line}</font>"
            elif line.startswith(("+++", "---")):
                return f"<font color='#000'>{line}</font>"
            elif line.startswith("+"):
                return f"<font color='#0A0'>{line}</font>"
            elif line.startswith("-"):
                return f"<font color='#A00'>{line}</font>"
            else:
                return f"<font color='#666'>{line}</font>"

        for index, diff in enumerate(diffs):
            msg = "{path}:\n<pre><code>{diff}</code></pre>".format(
                path=diff["new_path"],
                diff="\n".join(color_diff(line) for line in diff["diff"].split("\n")))
            await evt.respond(msg, reply=index == 0, allow_html=True)

    @commit.subcommand("log", help="Get the log of a specific repo.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=1)
    @OptRepoArgument("repo", "repository")
    @command.argument("page", "page", required=False, parser=optional_int)
    @command.argument("per_page", "entries per page", required=False, parser=optional_int)
    @with_gitlab_session
    async def log_cmd(self, evt: MessageEvent, repo: str, page: int, per_page: int,
                      gl: Gl) -> None:
        project = gl.projects.get(repo)
        commits = project.commits.list(page=page or 1, per_page=per_page or 10)

        def first_line(message: str) -> str:
            lines = message.strip().split("\n")
            message = lines[0][:80]
            if len(lines[0]) > 80:
                message += "…"
            elif len(lines) > 1:
                message += " (…)"
            return message

        await evt.reply("".join(f"* [`{commit.short_id}`]({gl.url}/{repo}/commit/{commit.id})"
                                f" {first_line(commit.message)}\n"
                                for commit in commits),
                        allow_html=True)

    @commit.subcommand("show", help="Get details about a specific commit.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @OptRepoArgument("repo", "repository")
    @command.argument("hash", "commit hash")
    @with_gitlab_session
    async def show(self, evt: MessageEvent, repo: str, hash: str, gl: Gl) -> None:
        project = gl.projects.get(repo)
        commit = project.commits.get(hash)
        date = (datetime
                .strptime(commit.committed_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                .strftime(self.bot.config["time_format"]))
        message = "\n".join(f"> {line}" for line in commit.message.strip().split("\n"))

        await evt.reply(f"Commit [`{commit.short_id}`]({gl.url}/{repo}/commit/{commit.id})"
                        f" by {commit.author_name} at {date}:\n\n{message}")
