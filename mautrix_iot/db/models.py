from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Room(Base):
    __tablename__ = "rooms"

    id = Column(String, primary_key=True)
    entity = relationship(
        "Entity",
        back_populates="room",
        lazy="subquery",
        uselist=False,
        cascade="all, delete-orphan",
    )
    user_matrix_id = Column(String)


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    host = Column(String)
    matrix_id = Column(String)
    description = Column(String)
    access_token = Column(String)

    is_device = Column(Boolean, default=True)

    room_id = Column(String, ForeignKey("rooms.id"), nullable=True)
    room = relationship(
        "Room",
        back_populates="entity",
        lazy="subquery",
        uselist=False,
    )
