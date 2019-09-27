import asyncio

from asyncio import Task

from typing import List, Type, Awaitable, Tuple, Optional

from aiohttp.web import Response, Request

from gitlab.exceptions import GitlabAuthenticationError
from gitlab import Gitlab as Gl

from maubot.handlers import event, web, command

from mautrix.types import (EventType, EventID, MessageType,
                           TextMessageEventContent, Format,
                           Membership)

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from maubot import Plugin, MessageEvent

from maubot.matrix import parse_markdown

from .gitlab_hook import EventParse

from .db import Database

from .util import OptArgument

from urllib.parse import urlparse


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("path")
        helper.copy("port")
        helper.copy("secret")
        helper.copy("base_command")
        helper.copy("send_as_notice")


class Gitlab(Plugin):

    def send_gitlab_event(self, room: str, msg: str) -> Awaitable[EventID]:
        if self.config['send_as_notice']:
            msgtype = MessageType.NOTICE
        else:
            msgtype = MessageType.TEXT

        content = TextMessageEventContent(msgtype=msgtype,
                                          body=msg
                                          )
        content.format = Format.HTML
        content.body, content.formatted_body = parse_markdown(content.body,
                                                              allow_html=True
                                                              )
        return self.client.send_message_event(room,
                                              EventType.ROOM_MESSAGE,
                                              content
                                              )

    async def process_hook(self, req: Request) -> None:
        if not req.has_body:
            self.log.debug('no body')
            return

        body = await req.json()

        if 'X-Gitlab-Event' not in req.headers:
            self.log.debug('missing X-Gitlab-Event Header')
            return None

        try:
            GitlabEvent = EventParse[req.headers['X-Gitlab-Event']].deserialize(body)  # noqa: E501

            msg = GitlabEvent.handle()
        except Exception as e:
            self.log.info("Failed to handle Gitlab event", exc_info=True)
            self.log.debug(e)
            msg = ''

        if msg:
            await self.send_gitlab_event(req.query['room'], msg)

        # make the typechecker happy
        task = asyncio.current_task()
        if task:
            self.task_list.remove(task)

    @web.post('/webhooks')
    async def post_handler(self, request: Request) -> Response:
        # check the authorisation of the request
        if 'X-Gitlab-Token' not in request.headers \
                or not request.headers['X-Gitlab-Token'] == self.config['secret']:  # noqa: E501
            resp_text = '403 FORBIDDEN'
            return Response(text=resp_text,
                            status=403
                            )

        # check if a roomid was specified
        if 'room' not in request.query:
            resp_text = 'No room specified. ' \
                        'Use example.com' + self.config['path'] + \
                        '?room=!<roomid>.'
            return Response(text=resp_text,
                            status=400
                            )

        # check if the bot is in the specified room
        if request.query['room'] not in self.joined_rooms:
            resp_text = 'The Bot is not in the room.'
            return Response(text=resp_text,
                            status=403
                            )

        # check if we can read the content of the request
        if 'Content-Type' not in request.headers \
                or not request.headers['Content-Type'] == 'application/json':
            self.log.debug(request.headers['Content-Type'])
            return Response(status=406,
                            headers={'Content-Type': 'application/json'}
                            )

        task = self.loop.create_task(self.process_hook(request))
        self.task_list += [task]

        return Response(status=202)

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

        self.joined_rooms = await self.client.get_joined_rooms()

        self.task_list: List[Task] = []

        self.db = Database(self.database)

    async def stop(self) -> None:
        for task in self.task_list:
            await asyncio.wait_for(task, timeout=1.0)
        # await self.runner.cleanup()

    @event.on(EventType.ROOM_MEMBER)
    async def member_handler(self, evt: MessageEvent) -> None:
        """
        updates the stored joined_rooms object whenever
        the bot joins or leaves a room.
        """
        if (evt.content.membership == Membership.LEAVE
                and evt.state_key == self.client.mxid):
            self.joined_rooms = await self.client.get_joined_rooms()
            self.log.info('left ' + str(evt.room_id))
        if (evt.content.membership == Membership.JOIN
                and evt.state_key == self.client.mxid):
            self.joined_rooms = await self.client.get_joined_rooms()
            self.log.info('joined ' + str(evt.room_id))

    @command.new(name="gitlab", help="Manage this Gitlab bot",
                 require_subcommand=True)
    async def gitlab(self) -> None:
        pass

    @gitlab.subcommand("ping", aliases=('p'),
                       help="Ping the bot.",)
    async def ping(self, evt: MessageEvent) -> None:
        await evt.reply("Pong")

    @gitlab.subcommand("server", aliases=("s"),
                       help="Manage Gitlab Servers.")
    async def server(self) -> None:
        pass

    @server.subcommand("login", aliases=("l"),
                       help="Add a Gitlab access token for a Gitlab server.")
    @command.argument("url", "Gitlab server URL")
    @command.argument("token", "Gitlab access token", pass_raw=True)
    async def server_login(self, evt: MessageEvent,
                           url: str, token: str) -> None:
        gl = Gl(url, private_token=token)
        try:
            gl.auth()
        except GitlabAuthenticationError:
            await evt.reply("Invalid access token!")
            return
        except Exception as e:
            await evt.reply("GitLab login failed: {0}".format(e))
            return
        self.db.add_login(evt.sender, url, token)
        msg = "Successfully logged into GitLab at {0} as {1}\n"
        await evt.reply(msg.format(url, gl.user.name))

    @server.subcommand("logout",
                       help="Remove the Gitlab access token and the"
                            "Gitlab server form the database.")
    @command.argument("url", "Gitlab server URL")
    async def server_logout(self, evt: MessageEvent, url: str) -> None:
        self.db.rm_login(evt.sender, url)
        await evt.reply("Removed {0} from the database.".format(url))

    @server.subcommand("list",
                       help="Show your Gitlab servers.")
    async def server_list(self, evt: MessageEvent) -> None:
        servers = self.db.get_servers(evt.sender)
        self.log.debug(servers)
        if not servers:
            await evt.reply("You are curently not logged in to any Server.")
            return
        msg: str = "You are currently loged in:\n\n"
        for server in servers:
            msg += "+ {0!s}\n".format(server)
        await evt.reply(msg)

    @server.subcommand("default",
                       help="Change your default Gitlab server.")
    @command.argument("url", "Gitlab server URL.")
    async def server_default(self, evt: MessageEvent, url: str) -> None:
        self.db.change_default(evt.sender, url)
        await evt.reply("Changed the default server to {0}".format(url))

    @gitlab.subcommand("alias", aliases=("a"),
                       help="Manage Gitlab server aliases.")
    async def alias(self) -> None:
        pass

    @alias.subcommand("add", aliases=("a"),
                      help="Add a alias to a Gitlab server.")
    @command.argument("url", "Gitlab Server URL")
    @command.argument("alias", "Gitlab Server alias")
    async def alias_add(self, evt: MessageEvent, url: str, alias: str) -> None:
        if url not in self.db.get_servers(evt.sender):
            await evt.reply("You can't add an alias to a "
                            "Gitlab server you are not logedin.")
            return
        aliases = [x[1] for x in self.db.get_aliases(evt.sender)]
        if alias in aliases:
            await evt.reply("Alias alredy in use.")
            return
        self.db.add_alias(evt.sender, url, alias)
        msg = "Added alias {0} to server {1}"
        await evt.reply(msg.format(alias, url))

    @alias.subcommand("rm",
                      help="Remove a alias to a Gitlab server.")
    @command.argument("alias", "Gitlab Server alias")
    async def alias_rm(self, evt: MessageEvent, alias: str) -> None:
        self.db.rm_alias(evt.sender, alias)
        await evt.reply("Removed alias {0}.".format(alias))

    @alias.subcommand("list", aliases=("l"),
                      help="Show your Gitlab server aliases.")
    async def alias_list(self, evt: MessageEvent) -> None:
        aliases = self.db.get_aliases(evt.sender)
        if not aliases:
            await evt.reply("You don't have any aliases.")
            return
        msg: str = "You have the following aliases:\n\n"
        for alias in aliases:
            msg += "+ {1} = {0}\n".format(*alias)
        await evt.reply(msg)

    @gitlab.subcommand("whoami",
                       help="Check who you're logged in as.")
    @command.argument('url_alias', "Gitlab Server URL or alias.",
                      required=False)
    async def whoami(self, evt: MessageEvent, url_alias: str = None) -> None:
        login = self.db.get_login(evt.sender, url_alias=url_alias)
        gl = Gl(login['gitlab_server'], private_token=login['api_token'])
        try:
            gl.auth()
        except GitlabAuthenticationError:
            await evt.reply("Invalid access token!")
            return
        except Exception as e:
            await evt.reply("Gitlab login failed: {0}".format(e))
            return
        msg = "You're logged  into {0} as [{3}]({1}/{2})"
        await evt.reply(msg.format(urlparse(gl._base_url).netloc,
                                   gl._base_url,
                                   gl.user.username,
                                   gl.user.name))

    @gitlab.subcommand("show",
                       help="Get details about a specific commit.")
    @OptArgument("url_alias", "Gitlab Server URL or alias.", arg_num=2)
    @command.argument("repo", "Gitlab Repository.")
    @command.argument("hash", "Gitlab Commit Hash.")
    async def show(self, evt: MessageEvent, repo: str,
                   hash: str, url_alias: str = None) -> None:
        login = self.db.get_login(evt.sender, url_alias=url_alias)
        with Gl(login['gitlab_server'], private_token=login['api_token']) as gl:
            project = gl.projects.get(repo)
            commit = project.commits.get(hash)
            repo_url = "{0}/{1}/commit/{2}".format(gl._base_url,
                                                   repo, commit.id)
        msg = "[{0}](Commit {1}) by {2} at {3}:\n\n> {4}"
        await evt.reply(msg.format(repo_url,
                                   commit.short_id,
                                   commit.author_name,
                                   # TODO: fix date format
                                   commit.committed_date,
                                   commit.message.replace("\n", "\n> ")))
        pass

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
