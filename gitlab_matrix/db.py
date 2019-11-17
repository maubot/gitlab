# gitlab - A GitLab client and webhook receiver for maubot
# Copyright (C) 2019 Lorenz Steinert
# Copyright (C) 2019 Tulir Asokan
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

from sqlalchemy import Column, String, Text, ForeignKeyConstraint, or_, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base

from mautrix.types import UserID, EventID, RoomID

AuthInfo = NamedTuple('AuthInfo', server=str, api_token=str)
AliasInfo = NamedTuple('AliasInfo', server=str, alias=str)
DefaultRepoInfo = NamedTuple('DefaultRepoInfo', server=str, repo=str)
Base = declarative_base()


class Token(Base):
    __tablename__ = "token"

    user_id: UserID = Column(String(255), primary_key=True, nullable=False)
    gitlab_server = Column(Text, primary_key=True, nullable=False)
    api_token = Column(Text, nullable=False)
    aliases = relationship("Alias", back_populates="token",
                           cascade="all, delete-orphan")
    default = relationship("Default", back_populates="token",
                           cascade="all, delete-orphan",
                           primaryjoin="Token.user_id==Default.user_id")


class Alias(Base):
    __tablename__ = "alias"

    user_id: UserID = Column(String(255), primary_key=True)
    gitlab_server = Column(Text, primary_key=True)
    alias = Column(Text, primary_key=True, nullable=False)
    __table_args__ = (ForeignKeyConstraint((user_id, gitlab_server),
                                           (Token.user_id, Token.gitlab_server)),)
    token = relationship("Token", back_populates="aliases")


class Default(Base):
    __tablename__ = "default"

    user_id: UserID = Column(String(255), ForeignKey("token.user_id"), primary_key=True)
    gitlab_server = Column(Text, ForeignKey("token.gitlab_server"))
    token = relationship("Token", back_populates="default",
                         primaryjoin="Token.user_id==Default.user_id")


class DefaultRepo(Base):
    __tablename__ = "default_repo"

    room_id: RoomID = Column(String(255), primary_key=True)
    server: str = Column(String(255), nullable=False)
    repo: str = Column(String(255), nullable=False)


class MatrixMessage(Base):
    __tablename__ = "matrix_message"

    message_id: str = Column(String(255), primary_key=True)
    room_id: RoomID = Column(String(255), primary_key=True)
    event_id: EventID = Column(String(255), nullable=False)


class Database:
    db: Engine

    def __init__(self, db: Engine) -> None:
        self.db = db
        Base.metadata.create_all(db)
        self.Session = sessionmaker(bind=self.db)

    def get_event(self, message_id: str, room_id: RoomID) -> Optional[EventID]:
        if not message_id:
            return None
        s: Session = self.Session()
        event = s.query(MatrixMessage).get((message_id, room_id))
        return event.event_id if event else None

    def put_event(self, message_id: str, room_id: RoomID, event_id: EventID) -> None:
        s: Session = self.Session()
        s.add(MatrixMessage(message_id=message_id, room_id=room_id, event_id=event_id))
        s.commit()

    def get_default_repo(self, room_id: RoomID) -> DefaultRepoInfo:
        s: Session = self.Session()
        default = s.query(DefaultRepo).get((room_id,))
        return DefaultRepoInfo(default.server, default.repo) if default else None

    def set_default_repo(self, room_id: RoomID, server: str, repo: str) -> None:
        s: Session = self.Session()
        s.merge(DefaultRepo(room_id=room_id, server=server, repo=repo))
        s.commit()

    def get_servers(self, mxid: UserID) -> List[str]:
        s = self.Session()
        rows = s.query(Token).filter(Token.user_id == mxid)
        return [row.gitlab_server for row in rows]

    def add_login(self, mxid: UserID, url: str, token: str) -> None:
        token_row = Token(user_id=mxid, gitlab_server=url, api_token=token)
        default = Default(user_id=mxid, gitlab_server=url)
        s = self.Session()
        try:
            s.add(token_row)
            s.query(Default).filter(Default.user_id == mxid).one()
        except NoResultFound:
            s.add(default)
        except MultipleResultsFound as e:
            log.warning("Multiple default servers found.")
            log.warning(e)
            raise e
        s.commit()

    def rm_login(self, mxid: UserID, url: str) -> None:
        s = self.Session()
        token = s.query(Token).get((mxid, url))
        s.delete(token)
        s.commit()

    def get_login(self, mxid: UserID, url_alias: str = None) -> AuthInfo:
        s = self.Session()
        if url_alias:
            row = (s.query(Token)
                   .join(Alias)
                   .filter(Token.user_id == mxid,
                           or_(Token.gitlab_server == url_alias,
                               Alias.alias == url_alias)).one())
        else:
            row = (s.query(Token)
                   .join(Default, Default.user_id == Token.user_id)
                   .filter(Token.user_id == mxid).one())
        return AuthInfo(server=row.gitlab_server, api_token=row.api_token)

    def get_login_by_server(self, mxid: UserID, url: str) -> AuthInfo:
        s = self.Session()
        row = s.query(Token).get((mxid, url))
        return AuthInfo(server=row.gitlab_server, api_token=row.api_token)

    def get_login_by_alias(self, mxid: UserID, alias: str) -> AuthInfo:
        s = self.Session()
        row = s.query(Token).join(Alias).filter(Token.user_id == mxid,
                                                Alias.alias == alias).one()
        return AuthInfo(server=row.gitlab_server, api_token=row.api_token)

    def add_alias(self, mxid: UserID, url: str, alias: str) -> None:
        s = self.Session()
        alias = Alias(user_id=mxid, gitlab_server=url, alias=alias)
        s.add(alias)
        s.commit()

    def rm_alias(self, mxid: UserID, alias: str) -> None:
        s = self.Session()
        alias = s.query(Alias).filter(Alias.user_id == mxid,
                                      Alias.alias == alias).one()
        s.delete(alias)
        s.commit()

    def has_alias(self, user_id: UserID, alias: str) -> bool:
        s: Session = self.Session()
        return s.query(Alias).filter(Alias.user_id == user_id, Alias.alias == alias).count() > 0

    def get_aliases(self, user_id: UserID) -> List[AliasInfo]:
        s = self.Session()
        rows = s.query(Alias).filter(Alias.user_id == user_id)
        return [AliasInfo(row.gitlab_server, row.alias) for row in rows]

    def get_aliases_per_server(self, user_id: UserID, url: str) -> List[AliasInfo]:
        s = self.Session()
        rows = s.query(Alias).filter(Alias.user_id == user_id,
                                     Alias.gitlab_server == url)
        return [AliasInfo(row.gitlab_server, row.alias) for row in rows]

    def change_default(self, mxid: UserID, url: str) -> None:
        s = self.Session()
        default = s.query(Default).get((mxid,))
        default.gitlab_server = url
        s.commit()
