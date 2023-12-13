# gitlab - A GitLab client and webhook receiver for maubot
# Copyright (C) 2019 Lorenz Steinert
# Copyright (C) 2019 Tulir Asokan
# Copyright (C) 2023 Thomas Ieong
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
from typing import List, NamedTuple, Optional
import logging as log

from mautrix.types import UserID, EventID, RoomID
from mautrix.util.async_db import Database

AuthInfo = NamedTuple('AuthInfo', server=str, api_token=str)
AliasInfo = NamedTuple('AliasInfo', server=str, alias=str)
DefaultRepoInfo = NamedTuple('DefaultRepoInfo', server=str, repo=str)


class DBManager:
    db: Database

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_event(self, message_id: str, room_id: RoomID) -> Optional[EventID]:
        if not message_id:
            return None
        q = (
            "SELECT message_id, room_id, event_id FROM matrix_message "
            "WHERE message_id = $1 AND room_id = $2"
        )
        event = await self.db.fetchrow(q, message_id, room_id)
        return event["event_id"] if event else None

    async def put_event(
            self,
            message_id: str,
            room_id: RoomID,
            event_id: EventID,
    ) -> None:
            q = (
                "INSERT INTO matrix_message (message_id, room_id, event_id) VALUES ($1, $2, $3) "
                "ON CONFLICT (message_id, room_id) DO UPDATE "
                "SET event_id = excluded.event_id"
            )
            await self.db.execute(q, message_id, room_id, event_id)

    async def get_default_repo(self, room_id: RoomID) -> DefaultRepoInfo:
        q = "SELECT room_id, server, repo FROM default_repo WHERE room_id = $1"
        default = await self.db.fetchrow(q, room_id)
        return DefaultRepoInfo(default["server"], default["repo"]) if default else None

    async def set_default_repo(self, room_id: RoomID, server: str, repo: str) -> None:
        q = (
            "INSERT INTO default_repo (room_id, server, repo) "
            "VALUES ($1, $2, $3) "
            "ON CONFLICT (room_id) DO UPDATE "
            "SET server = excluded.server, repo = excluded.repo"
        )
        await self.db.execute(q, room_id, server, repo)

    async def get_servers(self, mxid: UserID) -> List[str]:
        q = "SELECT user_id, gitlab_server, api_token FROM token WHERE user_id = $1"
        rows = await self.db.fetch(q, mxid)
        return [row["gitlab_server"] for row in rows]

    async def add_login(self, mxid: UserID, url: str, token: str) -> None:
        token_query = (
            "INSERT INTO token (user_id, gitlab_server, api_token) "
            "VALUES ($1, $2, $3)"
        )
        await self.db.execute(token_query, mxid, url, token)

        default_query = (
            "SELECT user_id, gitlab_server FROM 'default' "
            "WHERE user_id = $1"
        )
        result = await self.db.fetch(default_query, mxid)

        if len(result) > 1:
            log.warning("Multiple default servers found.")

        if not result:
            q = (
                "INSERT INTO 'default' (user_id, gitlab_server) "
                "VALUES ($1, $2)"
            )
            await self.db.execute(q, mxid, url)

    async def rm_login(self, mxid: UserID, url: str) -> None:
        q = "DELETE FROM token WHERE user_id = $1 AND gitlab_server = $2"
        await self.db.execute(q, mxid, url)

    async def get_login(self, mxid: UserID, url_alias: str = None) -> AuthInfo:
        if url_alias:
            q = (
                "SELECT user_id, gitlab_server, api_token FROM token "
                "JOIN alias ON token.user_id = alias.user_id "
                "AND token.gitlab_server = alias.gitlab_server "
                "WHERE token.user_id = $1 AND ( token.gitlab_server = $2 OR alias.alias = $2 )"
            )
            row = await self.db.fetchrow(q, mxid, url_alias)
        else:
            q = (
                "SELECT user_id, gitlab_server, api_token FROM token "
                "JOIN 'default' ON token.user_id = 'default'.user_id "
                "AND token.gitlab_server = 'default'.gitlab_server "
                "WHERE token.user_id = $1"
            )
            row = await self.db.fetchrow(q, mxid)
        return AuthInfo(server=row["gitlab_server"], api_token=row["api_token"])

    async def get_login_by_server(self, mxid: UserID, url: str) -> AuthInfo:
        q = (
            "SELECT user_id, gitlab_server, api_token FROM token "
            "WHERE user_id = $1 AND gitlab_server = $2"
        )
        row = await self.db.fetchrow(q, mxid, url)
        return AuthInfo(server=row["gitlab_server"], api_token=row["api_token"])

    async def get_login_by_alias(self, mxid: UserID, alias: str) -> AuthInfo:
        q = (
            "SELECT user_id, gitlab_server, api_token FROM token "
            "JOIN alias ON "
            "token.user_id = alias.user_id AND token.gitlab_server = alias.gitlab_server "
            "WHERE token.user_id = $1 AND alias.alias = $2"
        )
        row = await self.db.fetchrow(q, mxid, alias)
        return AuthInfo(server=row["gitlab_server"], api_token=row["api_token"])

    async def add_alias(self, mxid: UserID, url: str, alias: str) -> None:
        q = "INSERT INTO alias (user_id, gitlab_server, alias) VALUES ($1, $2, $3)"
        await self.db.execute(q, mxid, url, alias)

    async def rm_alias(self, mxid: UserID, alias: str) -> None:
        q = "DELETE FROM alias WHERE user_id = $1 AND alias = $2"
        await self.db.execute(q, mxid, alias)

    async def has_alias(self, user_id: UserID, alias: str) -> bool:
        q = (
            "SELECT user_id, gitlab_server, alias FROM alias "
            "WHERE user_id = $1 AND alias = $2"
        )
        rows = await self.db.fetch(q, user_id, alias)
        return len(rows) > 0

    async def get_aliases(self, user_id: UserID) -> List[AliasInfo]:
        q = (
            "SELECT user_id, gitlab_server, alias FROM alias "
            "WHERE user_id = $1"
        )
        rows = await self.db.fetch(q, user_id)
        return [AliasInfo(row["gitlab_server"], row["alias"]) for row in rows]

    async def get_aliases_per_server(self, user_id: UserID, url: str) -> List[AliasInfo]:
        q = (
            "SELECT user_id, gitlab_server, alias FROM alias "
            "WHERE user_id = $1 AND gitlab_server = $2"
        )
        rows = await self.db.fetch(q, user_id, url)
        return [AliasInfo(row["gitlab_server"], row["alias"]) for row in rows]

    async def change_default(self, mxid: UserID, url: str) -> None:
        q = (
            "SELECT user_id, gitlab_server FROM 'default' "
            "WHERE user_id = $1"
        )
        default = await self.db.fetchrow(q, mxid)
        if default:
            q = (
                "UPDATE 'default' SET gitlab_server = $2 "
                "WHERE user_id = $1"
            )
            await self.db.execute(q, mxid, url)

    async def get_webhook_room(self, secret: str) -> Optional[RoomID]:
        q = "SELECT room_id, secret FROM webhook_token WHERE secret = $1"
        webhook_token = await self.db.fetchrow(q, secret)
        return webhook_token["room_id"] if webhook_token else None

    async def add_webhook_room(self, secret: str, room_id: RoomID) -> None:
        q = "INSERT INTO webhook_token (room_id, secret) VALUES ($1, $2)"
        await self.db.execute(q, room_id, secret)
