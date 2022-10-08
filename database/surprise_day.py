from __future__ import annotations
from datetime import datetime, timedelta
import random
from sqlite3 import Connection
from typing import List, Tuple


def normalize_datetime(t: datetime):
    return t.replace(hour=0, minute=0, second=0)


def random_surprise_day(now):
    now = normalize_datetime(now)

    start_date = now + timedelta(days=7)

    end_date = now.replace(year=now.year + 1)
    end_date = end_date - timedelta(days=1)

    t = random.random()

    surprise_day = normalize_datetime(
        datetime.fromtimestamp(start_date.timestamp() * t + end_date.timestamp() * (1 - t))
    )
    return surprise_day


class SurpriseDay:
    def __init__(self, id: int, discord: str, message: str | None, channel: str | None, surprise_day: datetime, reset_day: datetime) -> None:
        self.id = id
        self.discord = discord
        self.message = message
        self.channel = channel
        self.surprise_day = surprise_day
        self.reset_day = reset_day

    def create(self, database: Connection) -> None:
        cur = database.cursor()
        res = cur.execute(
            "INSERT INTO surprise_days(discord, message, channel, surprise_day, reset_day) VALUES (?,?,?,?,?)",
            [self.discord, self.message, self.channel, int(self.surprise_day.timestamp()), int(self.reset_day.timestamp())],
        )
        self.id = res.lastrowid
        database.commit()

    def update_channel(self, database: Connection, channel: str | None):
        database.execute("UPDATE surprise_days SET channel = ? WHERE id = ?", (channel, self.id))
        database.commit()
        self.channel = channel

    def update_message(self, database: Connection, message: str | None):
        database.execute("UPDATE surprise_days SET message = ? WHERE id = ?", (message, self.id))
        database.commit()
        self.message = message

    def update_reset_day(self, database: Connection, reset_day: datetime) -> None:
        database.execute("UPDATE surprise_days SET reset_day = ? WHERE id = ?", [int(reset_day.timestamp()), self.id])
        database.commit()
        self.reset_day = reset_day

    def update_surprise_day(self, database: Connection, surprise_day: datetime) -> None:
        database.execute(
            "UPDATE surprise_days SET surprise_day = ? WHERE id = ?", [int(surprise_day.timestamp()), self.id]
        )
        database.commit()
        self.surprise_day = surprise_day

    @staticmethod
    def get_expired(database: Connection, now: datetime) -> List[SurpriseDay]:
        timestamp = int(now.timestamp())
        cur = database.cursor()
        res = cur.execute(
            """SELECT id, discord, message, channel, surprise_day, reset_day FROM surprise_days WHERE reset_day < ?;""",
            [timestamp],
        )
        return [
            SurpriseDay(id, discord, message, channel, datetime.fromtimestamp(surprise_day), datetime.fromtimestamp(reset_day))
            for (id, discord, message, channel, surprise_day, reset_day) in res.fetchall()
        ]

    @staticmethod
    def get_from_channel(database: Connection, channel: str) -> SurpriseDay | None:
        cur = database.cursor()
        res = cur.execute(
            """SELECT id, discord, message, channel, surprise_day, reset_day FROM surprise_days WHERE "channel"=?;""", [channel]
        )
        res = res.fetchone()
        if res == None:
            return None
        id, discord, message, channel, surprise_day, reset_day = res
        return SurpriseDay(
            id, discord, message, channel, datetime.fromtimestamp(surprise_day), datetime.fromtimestamp(reset_day)
        )

    @staticmethod
    def get_from_discord(database: Connection, discord: str) -> SurpriseDay | None:
        cur = database.cursor()
        res = cur.execute(
            """SELECT id, discord, message, channel, surprise_day, reset_day FROM surprise_days WHERE "discord"=?;""", [discord]
        )
        res = res.fetchone()
        if res == None:
            return None
        id, discord, message, channel, surprise_day, reset_day = res
        return SurpriseDay(
            id, discord, message, channel, datetime.fromtimestamp(surprise_day), datetime.fromtimestamp(reset_day)
        )

    @staticmethod
    def generate_surpriseday_and_resetday() -> Tuple[datetime, datetime]:
        now = normalize_datetime(datetime.now())
        surprise_day = random_surprise_day(now)
        reset_day = now.replace(year=now.year + 1)
        return (surprise_day, reset_day)

    @staticmethod
    def get_from_discord_or_default(database: Connection, discord: str) -> SurpriseDay:
        res = SurpriseDay.get_from_discord(database, discord)
        if res is not None:
            return res

        surprise_day, reset_day = SurpriseDay.generate_surpriseday_and_resetday()

        res = SurpriseDay(0, discord, None, None, surprise_day, reset_day)

        res.create(database)
        return res

    def __repr__(self) -> str:
        return "{} {} {} {}".format(self.id, self.discord, self.surprise_day, self.reset_day)

    @staticmethod
    def setup(database: Connection) -> None:
        database.execute(
            """CREATE TABLE IF NOT EXISTS "surprise_days" (
        "id"	INTEGER,
        "discord"	TEXT,
        "message"	TEXT,
        "channel"	TEXT,
        "surprise_day"	INTEGER,
        "reset_day"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT)
        );"""
        )
        database.commit()
