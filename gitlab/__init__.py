import asyncio

from typing import List, Type, Awaitable

from aiohttp import web

from maubot.handlers import event

from mautrix.types import (EventType, EventID, MessageType,
                           TextMessageEventContent, Format)

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from maubot import Plugin, MessageEvent

from maubot.matrix import parse_markdown

from .gitlab_hook import EventParse


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("path")
        helper.copy("port")
        helper.copy("secret")
        helper.copy("base_command")
        helper.copy("send_as_notice")


class Gitlab(Plugin):

    routes = web.RouteTableDef()

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

    async def process_hook(self, req: web.Request) -> None:
        if not req.has_body:
            self.log.debug('no body')
            return

        body = await req.json()

        if 'X-Gitlab-Event' not in req.headers:
            self.log.debug('missing X-Gitlab-Event Header')
            return None

        GitlabEvent = EventParse[req.headers['X-Gitlab-Event']](body)

        msg = GitlabEvent.handle()

        await self.send_gitlab_event(req.query['room'], msg)

    async def post_handler(self, request: web.Request) -> web.Response:
        # check the authorisation of the request
        if 'X-Gitlab-Token' not in request.headers \
                or not request.headers['X-Gitlab-Token'] == self.config['secret']:  # noqa: E501
            resp_text = '403 FORBIDDEN'
            return web.Response(text=resp_text,
                                status=403
                                )

        # check if a roomid was specified
        if 'room' not in request.query:
            resp_text = 'No room specified. ' \
                        'Use example.com' + self.config['path'] + \
                        '?room=!<roomid>.'
            return web.Response(text=resp_text,
                                status=400
                                )

        # check if the bot is in the specified room
        if request.query['room'] not in self.joined_rooms:
            resp_text = 'The Bot is not in the room.'
            return web.Response(text=resp_text,
                                status=403
                                )

        # check if we can read the content of the request
        if 'Content-Type' not in request.headers \
                or not request.headers['Content-Type'] == 'application/json':
            self.log.debug(request.headers['Content-Type'])
            return web.Response(status=406,
                                headers={'Content-Type': 'application/json'}
                                )

        task = self.loop.create_task(self.process_hook(request))
        self.task_list += [task]
        await task

        return web.Response(status=202)

    async def start(self) -> None:
        self.config.load_and_update()

        self.joined_rooms = await self.client.get_joined_rooms()

        self.task_list: List[asyncio.Task] = []

        self.app = web.Application()
        self.app.add_routes([web.post(self.config['path'], self.post_handler)])

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.sitev4 = web.TCPSite(self.runner, '0.0.0.0', self.config['port'])
        self.sitev6 = web.TCPSite(self.runner, '::', self.config['port'])
        await self.sitev4.start()
        await self.sitev6.start()

    async def stop(self) -> None:
        for task in self.task_list:
            await asyncio.wait_for(task, timeout=1.0)
        await self.runner.cleanup()

    @event.on(EventType.ROOM_MEMBER)
    async def member_handler(self, evt: MessageEvent) -> None:
        pass

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
