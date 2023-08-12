from typing import Optional

import sqlalchemy

from mautrix_iot.configuration import CONF
from mautrix_iot.db.database import Session
from mautrix_iot.db.models import Entity, Room


def get_bot_entity(session: Optional[Session] = None) -> Entity:
    with Session(session=session) as db:
        bot = (
            db.query(Entity)
            # .join(Room.entity)
            # .options(sqlalchemy.orm.joinedload(Entity.room))
            .filter(Entity.name == CONF.appservice["bot_username"]).first()
        )

    print(bot.room)
    return bot


def update_bot_room(
    room_id: str, bot_matrix_id: str, session: Optional[Session] = None
) -> Room:
    with Session(session=session) as db:
        bot = db.query(Entity).filter(Entity.matrix_id == bot_matrix_id).first()
        if bot is None:
            raise ValueError(f"No such bot: {bot_matrix_id}")

        room = db.query(Room).filter(Room.id == room_id).first()
        if room is None:
            room = Room(id=room_id, entity=bot)
            db.add(room)

        bot.room = room

    return room


def delete_bot_room(session: Optional[Session] = None) -> None:
    with Session(session=session) as db:
        bot = get_bot_entity(db)
        if not bot.room:
            return

        room = db.query(Room).filter(Room.id == bot.room.id)
        room.delete()
