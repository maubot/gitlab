import asyncio

from typing import List, Type

from aiohttp import web

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from maubot import Plugin


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("path")
        helper.copy("port")
        helper.copy("secret")
        helper.copy("base_command")


class Gitlab(Plugin):

    routes = web.RouteTableDef()

    async def process_hook(self, request: web.Request) -> None:
        if not request.has_body():
            await self.client.send_text(request.query['room'],
                                        "Webhook doesn't have a Body.")
        self.log.debug(str(request))
        self.log.debug(str(request.query['room']))
        await self.client.send_text(request.query['room'], str(request))

    async def post_handler(self, request: web.Request) -> web.Response:
        # check the authorisation of the request
        if 'X-Gitlab-Token' not in request.headers \
                or not request.headers['X-Gitlab-Token'] == self.config['secret']:
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
        # TODO: make joined_rooms a clas property which is updated on startup and room join/leave
        joined_rooms = await self.client.get_joined_rooms()
        if request.query['room'] not in joined_rooms:
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
        self.task_list.append(asyncio.create_task(self.process_hook(request)))

        return web.Response(status=202)

    async def start(self) -> None:
        self.config.load_and_update()

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

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
