import asyncio

from asyncio import Task

from typing import List, Type, Awaitable

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
                       help="Show your Gitlab servers.")
    async def server(self) -> None:
        pass

    @server.subcommand("login", aliases=("l"),
                       help="Add a Gitlab access token for a Gitlab server.")
    @command.argument("url", "Gitlab server URL")
    @command.argument("token", "Gitlab access token")
    async def server_login(self, evt: MessageEvent,
                           url: str, token: str) -> None:
        gl = Gl(url, private_token=token)
        try:
            gl.auth()
            self.db.add_login(evt.sender, url, token)
        except GitlabAuthenticationError:
            await evt.reply("Invalid access token!")
            return
        except Exception as e:
            await evt.reply("GitLab login failed: {0}".format(e))
            return
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
            msg += " + {0!s}\n".format(server)
        await evt.reply(msg)

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
