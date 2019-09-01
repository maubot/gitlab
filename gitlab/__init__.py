import asyncio

from typing import List, Type, Awaitable

from aiohttp import web

from maubot.handlers import event

from mautrix.types import (EventType, EventID, MessageType, TextMessageEventContent, Format)

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

from maubot import Plugin, MessageEvent

from maubot.matrix import parse_markdown


def handlePushEvent(body) -> str:
    branch = body['ref'].replace('refs/heads/', '')

    if int(body['total_commits_count']) == 0:
        msg = "\[{2!s}/{3!s}\] {4!s} force pushed to" \
                   "or deleted branch [{1!s}]({0!s}/tree/{1!s})"
        return msg.format(body['project']['web_url'],
                          branch,
                          body['project']['namespace'],
                          body['project']['name'],
                          body['user_username']
                          )

    pluralizer: str = ''
    if int(body['total_commits_count']) != 1:
        pluralizer = 's'

    msg = "\[[{2!s}/{3!s}]({0!s}/tree/{1!s})\] " \
          "{4:d} new commit{6!s} by {5!s}\n\n"
    msg = msg.format(body['project']['web_url'],
                     branch,
                     body['project']['namespace'],
                     body['project']['name'],
                     body['total_commits_count'],
                     body['user_username'],
                     pluralizer
                     )

    for commit in reversed(body['commits']):
        lines = commit['message'].split('\n')
        if len(lines) > 1 and len(''.join(lines[1:])) > 0:
            lines[0] += " (...)"
        msg += "+ {0!s} ({1!s})\n".format(lines[0], commit['id'][:8])

    return msg


def handleTagEvent(body):
    pass


def handleIssueEvent(body):
    pass


def handleNoteEvent(body):
    pass


def handleMergeRequestEvent(body):
    pass


def handleWikiPageEvent(body):
    pass


def handlePipelineEvent(body):
    pass


EventParse = {'Push Hook': handlePushEvent,
              'Tag Push Hook': handleTagEvent,
              'Issue Hook': handleIssueEvent,
              'Note Hook': handleNoteEvent,
              'Merge Request Hook': handleMergeRequestEvent,
              'Wiki Page Hook': handleWikiPageEvent,
              'Pipeline Hook': handlePipelineEvent
              }


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

        GitlabEvent = req.headers['X-Gitlab-Event']

        msg = EventParse[GitlabEvent](body)

        await self.send_gitlab_event(req.query['room'], msg)

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
