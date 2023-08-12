from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mautrix_iot.configuration import CONF
from mautrix_iot.db.models import Entity
from mautrix_iot.utils import bot_full_name

engine = create_engine(
    CONF.appservice["database"], connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Session:
    def __init__(self, session: Optional["Session"] = None):
        self.session_maker = SessionLocal
        self.session = session

    def __enter__(self, *args, **kwargs):
        if not self.session:
            self.session = self.session_maker()
        return self.session

    def __exit__(self, *args, **kwargs):
        if self.session:
            self.session.flush()
            self.session.expunge_all()
            self.session.commit()
            self.session.close()


def get_entity_for_room(room_id: str) -> Optional[Entity]:
    with Session() as db:
        return db.query(Entity).filter(Entity.room_id == room_id).first()


def get_bot_entity() -> Entity:
    with Session() as db:
        bot = db.query(Entity).filter(Entity.is_device == False).first()

    if bot is None:
        raise Exception("No default bot in database")

    return bot


def _initial_db_population():
    with Session() as session:
        if (
            not session.query(Entity)
            .filter(Entity.name == CONF.appservice["bot_username"])
            .first()
        ):
            session.add(
                Entity(
                    name=CONF.appservice["bot_username"],
                    description="Mautrix IoT Bot",
                    matrix_id=bot_full_name(),
                    is_device=False,
                )
            )
