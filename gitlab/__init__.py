from typing import Type

from aiohttp import web

from mautrix.types import EventType

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from maubot import Plugin, MessageEvent

from maubot.handlers import event


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("path")
        helper.copy("port")
        helper.copy("secret")
        helper.copy("base_command")


class Gitlab(Plugin):

    routes = web.RouteTableDef()

    async def post_handler(self, request):
        if not request.headers['X-Gitlab-Token'] == self.config['secret']:
            self.log.warn('unauthorised access')
            return web.Response()
        self.log.debug(str(request))
        self.log.debug(str(request.query['room']))
        await self.client.send_text(request.query['room'], str(request))
        return web.Response()

    async def start(self) -> None:
        self.config.load_and_update()

        self.app = web.Application()
        self.app.add_routes([web.post(self.config['path'], self.post_handler)])

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', self.config['port'])
        await site.start()

    async def stop(self) -> None:
        await self.runner.cleanup()

    @event.on(EventType.ROOM_MESSAGE)
    async def handler(self, event: MessageEvent) -> None:
        if event.sender != self.client.mxid:
            for ii in ['path', 'port', 'secret', 'base_command']:
                await self.client.send_text(event.room_id, str(self.config[ii]))

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
