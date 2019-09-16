from typing import List, Tuple

from sqlalchemy import (Column, String, Text,
                        ForeignKeyConstraint, or_,
                        ForeignKey)
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base

from mautrix.types import UserID

import logging as log

Base = declarative_base()


class Token(Base):
    __tablename__ = "token"

    user_id = Column(String(255), primary_key=True, nullable=False)
    gitlab_server = Column(Text, primary_key=True, nullable=False)
    api_token = Column(Text, nullable=False)
    aliases = relationship("Alias", back_populates="token",
                           cascade="all, delete-orphan")
    default = relationship("Default", back_populates="token",
                           cascade="all, delete-orphan")


class Alias(Base):
    __tablename__ = "alias"

    user_id = Column(String(255), primary_key=True)
    gitlab_server = Column(Text, primary_key=True)
    alias = Column(Text, primary_key=True, nullable=False)
    __table_args__ = (ForeignKeyConstraint([user_id,
                                            gitlab_server],
                                           [Token.user_id,
                                            Token.gitlab_server]),
                      {})
    token = relationship("Token", back_populates="aliases")


class Default(Base):
    __tablename__ = "default"

    user_id = Column(String(255), ForeignKey('token.user_id'),
                     primary_key=True)
    gitlab_server = Column(Text, ForeignKey('token.gitlab_server'))
    token = relationship("Token", back_populates="default")


class Database:
    db: Engine

    def __init__(self, db: Engine) -> None:
        self.db = db
        Base.metadata.create_all(db)
        self.Session = sessionmaker(bind=self.db)

    def get_servers(self, mxid: UserID) -> List[str]:
        s = self.Session()
        rows = s.query(Token).filter(Token.user_id == mxid)

        servers = [row.gitlab_server for row in rows]

        return servers

    def add_login(self, mxid: str, url: str, token: str) -> None:
        token_row = Token(user_id=mxid, gitlab_server=url, api_token=token)
        default = Default(user_id=mxid, gitlab_server=url)
        s = self.Session()
        try:
            s.add(token_row)
            s.query(Default).filter(Default.user_id == mxid).one()
        except NoResultFound:
            s.add(default)
        except MultipleResultsFound as e:
            log.warn("Multiple Default Servers found.")
            log.warn(e)
            raise e
        s.commit()

    def rm_login(self, mxid: UserID, url: str) -> None:
        s = self.Session()
        token = s.query(Token).get((mxid, url))
        s.delete(token)
        s.commit()

    def get_login(self, mxid: UserID,
                  url_alias: str = None) -> Tuple[str, str]:
        s = self.Session()
        if url_alias:
            row = (s.query(Token).join(Alias)
                    .filter(Token.user_id == mxid,
                            or_(Token.gitlab_server == url_alias,
                                Alias.alias == url_alias)).one())
        else:
            row = (s.query(Token).join(Default)
                    .filter(Token.user_id == mxid).one())
        return (row.gitlab_server, row.api_token)

    def get_login_by_server(self, mxid: UserID, url: str) -> Tuple[str, str]:
        s = self.Session()
        row = s.query(Token).get((mxid, url))
        return (row.gitlab_server, row.api_token)

    def get_login_by_alias(self, mxid: str, alias: str) -> Tuple[str, str]:
        s = self.Session()
        row = s.query(Token).join("aliases").filter(Token.user_id == mxid,
                                                    Alias.alias == alias).one()
        return (row.gitlab_server, row.api_token)

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

    def get_aliases(self, user_id: UserID) -> List[Tuple[str, str]]:
        s = self.Session()
        rows = s.query(Alias).filter(Alias.user_id == user_id)
        return [(row.gitlab_server, row.alias) for row in rows]

    def get_aliases_per_server(self, user_id: UserID,
                               url: str) -> List[Tuple[str, str]]:
        s = self.Session()
        rows = s.query(Alias).filter(Alias.user_id == user_id,
                                     Alias.gitlab_server == url)
        return [(row.gitlab_server, row.alias) for row in rows]

    def change_default(self, mxid: UserID, url: str) -> None:
        s = self.Session()
        default = s.query(Default).get((mxid,))
        default.gitlab_server = url
        s.commit()
