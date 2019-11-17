from typing import List, Set, Type
from datetime import datetime
from functools import partial
from asyncio import Task
import asyncio
import re

from aiohttp.web import Response, Request
from yarl import URL

from gitlab.exceptions import GitlabAuthenticationError
from gitlab import Gitlab as Gl

from mautrix.types import EventType, RoomID, MessageType, StateEvent, Membership
from mautrix.util.config import BaseProxyConfig
from maubot import Plugin, MessageEvent
from maubot.handlers import event, web, command

from .gitlab_hook import EventParse
from .db import Database
from .util import (OptUrlAliasArgument, with_gitlab_session, Config, optional_int, quote_parser,
                   sigil_int)


class GitlabBot(Plugin):
    joined_rooms: Set[RoomID]
    task_list: List[Task]
    db: Database

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

        self.joined_rooms = set(await self.client.get_joined_rooms())
        self.task_list = []
        self.db = Database(self.database)

    async def stop(self) -> None:
        if self.task_list:
            await asyncio.wait(self.task_list, timeout=1)

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @event.on(EventType.ROOM_MEMBER)
    async def member_handler(self, evt: StateEvent) -> None:
        """
        updates the stored joined_rooms object whenever
        the bot joins or leaves a room.
        """
        if evt.state_key != self.client.mxid:
            return

        if evt.content.membership in (Membership.LEAVE, Membership.BAN):
            self.joined_rooms.remove(evt.room_id)
        if evt.content.membership == Membership.JOIN and evt.state_key == self.client.mxid:
            self.joined_rooms.add(evt.room_id)

    # region Webhook handling

    @web.post("/webhooks")
    async def post_handler(self, request: Request) -> Response:
        if "X-Gitlab-Token" not in request.headers:
            return Response(text="401: Unauthorized\n"
                                 "Missing auth token header\n", status=401)
        if "X-Gitlab-Event" not in request.headers:
            return Response(text="400: Bad request\n"
                                 "Event type not specified\n", status=400)

        if request.headers["X-Gitlab-Token"] != self.config["secret"]:
            return Response(text="401: Unauthorized\n", status=401)

        if "room" not in request.query:
            return Response(text="400: Bad request\n"
                                 "No room specified. Did you forget the ?room query parameter?\n",
                            status=400)

        if not request.can_read_body:
            return Response(status=400, text="400: Bad request\n"
                                             "Missing request body\n")

        if request.query["room"] not in self.joined_rooms:
            return Response(text="403: Forbidden\nThe bot is not in the room. "
                                 f"Please invite {self.client.mxid} to the room.\n", status=403)

        if request.headers.getone("Content-Type", "") != "application/json":
            return Response(status=406, text="406: Not Acceptable\n",
                            headers={"Accept": "application/json"})

        task = self.loop.create_task(self.process_hook(request))
        self.task_list += [task]

        return Response(status=202, text="202: Accepted\nWebhook processing started.\n")

    async def process_hook(self, req: Request) -> None:
        body = await req.json()

        if self.config["send_as_notice"]:
            msgtype = MessageType.NOTICE
        else:
            msgtype = MessageType.TEXT

        try:
            evt = EventParse[req.headers["X-Gitlab-Event"]].deserialize(body)
            room_id = RoomID(req.query["room"])
            edit_evt = self.db.get_event(evt.matrix_message_edit_id, room_id)
            if evt.has_matrix_message:
                event_id = await self.client.send_markdown(room_id, evt.matrix_message,
                                                           allow_html=True, edits=edit_evt,
                                                           msgtype=msgtype)
                if not edit_evt and evt.matrix_message_edit_id:
                    self.db.put_event(evt.matrix_message_edit_id, room_id, event_id)
        except Exception:
            self.log.error("Failed to handle Gitlab event", exc_info=True)

        task = asyncio.current_task()
        if task:
            self.task_list.remove(task)

    # endregion

    @command.new(name="gitlab", help="Manage this Gitlab bot",
                 require_subcommand=True)
    async def gitlab(self) -> None:
        pass

    # region !gitlab server

    @gitlab.subcommand("server", aliases=("s",), help="Manage GitLab Servers.")
    async def server(self) -> None:
        pass

    @server.subcommand("default", aliases=("d",), help="Change your default GitLab server.")
    @command.argument("url", "server URL")
    async def server_default(self, evt: MessageEvent, url: str) -> None:
        self.db.change_default(evt.sender, url)
        await evt.reply(f"Changed the default server to {url}")

    @server.subcommand("list", aliases=("ls",), help="Show your GitLab servers.")
    async def server_list(self, evt: MessageEvent) -> None:
        servers = self.db.get_servers(evt.sender)
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
            self.log.warning(f"Unexpected error logging into GitLab {url} for {evt.sender}",
                             exc_info=True)
            await evt.reply(f"GitLab login failed: {e}")
            return
        self.db.add_login(evt.sender, url, token)
        await evt.reply(f"Successfully logged into GitLab at {url} as {gl.user.name}")

    @server.subcommand("logout", help="Remove the access token from the bot's database.")
    @command.argument("url", "server URL")
    async def server_logout(self, evt: MessageEvent, url: str) -> None:
        self.db.rm_login(evt.sender, url)
        await evt.reply(f"Removed {url} from the database.")

    # endregion
    # region !gitlab alias

    @gitlab.subcommand("alias", aliases=("a",),
                       help="Manage Gitlab server aliases.")
    async def alias(self) -> None:
        pass

    @alias.subcommand("add", aliases=("a",), help="Add a alias to a GitLab server.")
    @command.argument("url", "server URL")
    @command.argument("alias", "server alias")
    async def alias_add(self, evt: MessageEvent, url: str, alias: str) -> None:
        if url not in self.db.get_servers(evt.sender):
            await evt.reply("You can't add an alias to a GitLab server you are not logged in to.")
            return
        if self.db.has_alias(evt.sender, alias):
            await evt.reply("Alias already in use.")
            return
        self.db.add_alias(evt.sender, url, alias)
        await evt.reply(f"Added alias {alias} to server {url}")

    @alias.subcommand("list", aliases=("l", "ls"), help="Show your Gitlab server aliases.")
    async def alias_list(self, evt: MessageEvent) -> None:
        aliases = self.db.get_aliases(evt.sender)
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
        self.db.rm_alias(evt.sender, alias)
        await evt.reply(f"Removed alias {alias}.")

    # endregion
    # region !gitlab issue

    @gitlab.subcommand("issue", help="Manage GitLab issues.")
    async def issue(self) -> None:
        pass

    @issue.subcommand("close", help="Close an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @command.argument("repo", "repository")
    @command.argument("id", "issue ID")
    @with_gitlab_session
    async def issue_close(self, evt: MessageEvent, repo: str, id: str, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)
        issue.state_event = "close"
        issue.save()

        await evt.reply(f"Closed issue #{issue.iid}: {issue.title}")

    @issue.subcommand("comment", help="Write a commant on an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=3)
    @command.argument("repo", "repository")
    @command.argument("id", "issue ID", parser=sigil_int)
    @command.argument("body", "comment body", pass_raw=True)
    @with_gitlab_session
    async def issue_comment(self, evt: MessageEvent, repo: str, id: int, body: str, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)
        issue.notes.create({"body": body.strip()})

        await evt.reply(f"Commented on issue #{issue.iid}: {issue.title}")

    @issue.subcommand("comments", aliases=("read-comments",),
                      help="Write a commant on an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @command.argument("repo", "repository")
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
                    .strftime(self.config["time_format"]))
            author = note.author["name"]
            return f"{author} at {date}:\n{body}"

        await evt.reply("\n\n".join(format_note(note) for note in reversed(notes)))

    @issue.subcommand("create", help="Create an Issue. The issue body can be placed on a new line.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=3)
    @command.argument("repo", "repository")
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
    @command.argument("repo", "repository")
    @command.argument("id", "issue ID", parser=sigil_int)
    @with_gitlab_session
    async def issue_read(self, evt: MessageEvent, repo: str, id: int, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)

        msg = f"Issue #{issue.iid} by {issue.author['name']}: [{issue.title}]({issue.web_url})  \n"
        names = [assignee.name for assignee in issue.assignees]
        if len(names) > 1:
            msg += f"Assigned to {', '.join(names[:-1])} and {names[-1]}.  \n"
        elif len(names) == 1:
            msg += f"Assigned to {names[0]}.  \n"
        msg += "\n".join(f"> {line}" for line in issue.description.strip().split("\n"))

        await evt.reply(msg)

    @issue.subcommand("reopen", help="Reopen an issue.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @command.argument("repo", "repository")
    @command.argument("id", "issue ID", parser=sigil_int)
    @with_gitlab_session
    async def issue_reopen(self, evt: MessageEvent, repo: str, id: int, gl: Gl) -> None:
        project = gl.projects.get(repo)
        issue = project.issues.get(id)
        issue.state_event = "reopen"
        issue.save()

        await evt.reply(f"Reopened issue #{issue.iid}: {issue.title}")

    # endregion
    # region Commit info (diff, log, show)

    @gitlab.subcommand("diff", help="Get the diff of a specific commit.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @command.argument("repo", "repository")
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

    @gitlab.subcommand("log",
                       help="Get the log of a specific repo.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=1)
    @command.argument("repo", "repository")
    @command.argument("page", "page", required=False, parser=optional_int)
    @command.argument("per_page", "entries per page", required=False, parser=optional_int)
    @with_gitlab_session
    async def log(self, evt: MessageEvent, repo: str, page: int, per_page: int, gl: Gl) -> None:
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

    @gitlab.subcommand("show", help="Get details about a specific commit.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=2)
    @command.argument("repo", "repository")
    @command.argument("hash", "commit hash")
    @with_gitlab_session
    async def show(self, evt: MessageEvent, repo: str, hash: str, gl: Gl) -> None:
        project = gl.projects.get(repo)
        commit = project.commits.get(hash)
        date = (datetime
                .strptime(commit.committed_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                .strftime(self.config["time_format"]))
        message = "\n".join(f"> {line}" for line in commit.message.strip().split("\n"))

        await evt.reply(f"Commit [`{commit.short_id}`]({gl.url}/{repo}/commit/{commit.id})"
                        f" by {commit.author_name} at {date}:\n\n{message}")

    # endregion
    # region Auth extras (ping, whoami)

    @gitlab.subcommand("ping", aliases=("p",), help="Ping the bot.")
    async def ping(self, evt: MessageEvent) -> None:
        await evt.reply("Pong")

    @gitlab.subcommand("whoami", help="Check who you're logged in as.")
    @OptUrlAliasArgument("login", "server URL or alias", arg_num=0)
    @with_gitlab_session
    async def whoami(self, evt: MessageEvent, gl: Gl) -> None:
        gl.auth()
        await evt.reply(f"You're logged into {URL(gl.url).host} as "
                        f"[{gl.user.name}]({gl.url}/{gl.user.username})")

    # endregion
