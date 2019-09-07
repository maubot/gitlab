from typing import List, Tuple

from sqlalchemy import (Column, String, Text,
                        ForeignKeyConstraint)
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base

from mautrix.types import UserID

Base = declarative_base()


class Token(Base):
    __tablename__ = "token"

    user_id = Column(String(255), primary_key=True, nullable=False)
    gitlab_server = Column(Text, primary_key=True, nullable=False)
    api_token = Column(Text, nullable=False)
    aliases = relationship("Alias", back_populates="token",
                           cascade="all, delete-orphan")


class Alias(Base):
    __tablename__ = "alias"

    user_id = Column(String(255), primary_key=True)
    gitlab_server = Column(Text, primary_key=True)
    alias = Column(Text, nullable=False)
    __table_args__ = (ForeignKeyConstraint([user_id,
                                            gitlab_server],
                                           [Token.user_id,
                                            Token.gitlab_server]),
                      {})
    token = relationship("Token", back_populates="aliases")


class Database:
    db: Engine

    def __init__(self, db: Engine) -> None:
        self.db = db
        Base.metadata.create_all(db)
        self.Session = sessionmaker(bind=self.db)

    def get_servers(self, mxid: UserID) -> List[str]:
        s = self.Session()
        rows = (s.query(Token).filter(Token.user_id == mxid))

        servers = [row.gitlab_server for row in rows]

        return servers

    def add_login(self, user_id: str, url: str, token: str) -> None:
        token = Token(user_id, url, token)
        s = self.Session()
        s.add(token)
        s.commit()

    def rm_login(self, mxid: UserID, url: str) -> None:
        s = self.Session()
        token = s.query(Token).get((mxid, url))
        s.delete(token)
        s.commit()

    def get_login(self, mxid: UserID, url: str) -> Tuple[str, str]:
        s = self.Session()
        row = s.query(Token).filter(Token.user_id == mxid,
                                    Token.gitlab_server == url).one()
        return (row.gitlab_server, row.api_token)
