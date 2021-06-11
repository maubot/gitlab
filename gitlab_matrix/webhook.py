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
import json
from typing import List, Set, TYPE_CHECKING
from asyncio import Task
import asyncio
import re

import attr
from jinja2 import TemplateNotFound
from aiohttp.web import Response, Request

from mautrix.types import (EventType, RoomID, StateEvent, Membership, MessageType, JSON,
                           TextMessageEventContent, Format)
from mautrix.util.formatter import parse_html
from maubot.handlers import web, event

from .types import EventParse, Action, OTHER_ENUMS
from .util import TemplateManager, TemplateUtil

if TYPE_CHECKING:
    from .bot import GitlabBot

import pprint

spaces = re.compile(" +")
space = " "


class GitlabWebhook:
    bot: 'GitlabBot'
    task_list: List[Task]
    joined_rooms: Set[RoomID]
    messages: TemplateManager
    templates: TemplateManager

    def __init__(self, bot: 'GitlabBot') -> None:
        self.bot = bot
        self.task_list = []
        self.joined_rooms = set()

        self.messages = TemplateManager(self.bot.loader, "templates/messages")
        self.templates = TemplateManager(self.bot.loader, "templates/mixins")

    async def start(self) -> 'GitlabWebhook':
        self.joined_rooms = set(await self.bot.client.get_joined_rooms())
        return self

    async def stop(self) -> None:
        if self.task_list:
            await asyncio.wait(self.task_list, timeout=1)

    @web.post("/webhooks")
    async def post_handler(self, request: Request) -> Response:
        try:
            token = request.headers["X-Gitlab-Token"]
        except KeyError:
            return Response(text="401: Unauthorized\n"
                                 "Missing auth token header\n", status=401)
        else:
            if token != self.bot.config["secret"]:
                return Response(text="401: Unauthorized\n", status=401)

        try:
            evt_type = request.headers["X-Gitlab-Event"]
        except KeyError:
            return Response(text="400: Bad request\n"
                                 "Event type not specified\n", status=400)

        try:
            room_id = RoomID(request.query["room"])
        except KeyError:
            return Response(text="400: Bad request\n"
                                 "No room specified. Did you forget the ?room query parameter?\n",
                            status=400)

        if not request.can_read_body:
            return Response(status=400, text="400: Bad request\n"
                                             "Missing request body\n")

        if room_id not in self.joined_rooms:
            return Response(text="403: Forbidden\nThe bot is not in the room. "
                                 f"Please invite {self.bot.client.mxid} to the room.\n",
                            status=403)

        if request.headers.getone("Content-Type", "") != "application/json":
            return Response(status=406, text="406: Not Acceptable\n",
                            headers={"Accept": "application/json"})

        try:
            body = await request.json()
        except json.JSONDecodeError:
            return Response(status=406, text="400: Bad Request\nBody is not valid JSON\n",
                            headers={"Accept": "application/json"})

        self.bot.log.trace("Accepted processing of %s", request.headers["X-Gitlab-Event"])
        task = asyncio.create_task(self.try_process_hook(body, evt_type, room_id))
        self.task_list += [task]

        return Response(status=202, text="202: Accepted\nWebhook processing started.\n")

    async def try_process_hook(self, body: JSON, evt_type: str, room_id: RoomID) -> None:
        try:
            await self.process_hook(body, evt_type, room_id)
        except Exception:
            self.bot.log.warning("Failed to process webhook", exc_info=True)
        finally:
            try:
                task = asyncio.current_task()
            except RuntimeError:
                task = None
            if task:
                self.task_list.remove(task)

    async def process_hook(self, body: JSON, evt_type: str, room_id: RoomID) -> None:
        pprint.pprint(body)  # FIXME remove

        msgtype = MessageType.NOTICE if self.bot.config["send_as_notice"] else MessageType.TEXT
        evt = EventParse[evt_type].deserialize(body)

        try:
            tpl = self.messages[evt.template_name]
        except TemplateNotFound:
            self.bot.log.debug(f"Unhandled {evt_type} from GitLab")
            return

        aborted = False

        def abort() -> None:
            nonlocal aborted
            aborted = True

        base_args = {
            **{field.key: field for field in Action if field.key.isupper()},
            **OTHER_ENUMS,
            "abort": abort,
            "util": TemplateUtil,
        }

        for subevt in evt.preprocess():
            args = {
                **attr.asdict(subevt, recurse=False),
                **{key: getattr(subevt, key) for key in subevt.event_properties},
                **base_args,
            }
            args["templates"] = self.templates.proxy(args)

            html = tpl.render(**args)
            if not html or aborted:
                aborted = False
                continue
            html = spaces.sub(space, html.strip())

            content = TextMessageEventContent(msgtype=msgtype, format=Format.HTML,
                                              formatted_body=html, body=parse_html(html))
            content["xyz.maubot.gitlab.webhook"] = {
                "event_type": evt_type,
                **subevt.meta,
            }
            pprint.pprint(content)  # FIXME remove

            edit_evt = self.bot.db.get_event(subevt.matrix_message_edit_id, room_id)
            if edit_evt:
                content.set_edit(edit_evt)
            event_id = await self.bot.client.send_message(room_id, content)
            if not edit_evt and subevt.matrix_message_edit_id:
                self.bot.db.put_event(subevt.matrix_message_edit_id, room_id, event_id)

    @event.on(EventType.ROOM_MEMBER)
    async def member_handler(self, evt: StateEvent) -> None:
        """
        updates the stored joined_rooms object whenever
        the bot joins or leaves a room.
        """
        if evt.state_key != self.bot.client.mxid:
            return

        if evt.content.membership in (Membership.LEAVE, Membership.BAN):
            self.joined_rooms.remove(evt.room_id)
        if evt.content.membership == Membership.JOIN and evt.state_key == self.bot.client.mxid:
            self.joined_rooms.add(evt.room_id)
