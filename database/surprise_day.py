from __future__ import annotations
from datetime import datetime, timedelta
import random
from sqlite3 import Connection

def normalize_datetime(t: datetime):
    return t.replace(hour=0, minute=0, second=0)

def random_surprise_day(now):
    now = normalize_datetime(now)

    next_year = now.replace(year=now.year + 1)
    next_year = next_year-timedelta(days=1)

    t = random.random()

    surprise_day = normalize_datetime(datetime.fromtimestamp(now.timestamp()*t+next_year.timestamp()*(1-t)))
    return surprise_day

class SurpriseDay:
    def __init__(self, id: int, discord: str, channel: str, surprise_day: datetime, reset_day: datetime) -> None:
        self.id = id
        self.discord = discord
        self.channel = channel
        self.surprise_day = surprise_day
        self.reset_day = reset_day
    
    def create(self, database: Connection) -> None:
        cur = database.cursor()
        res = cur.execute("INSERT INTO surprise_days(discord, channel, surprise_day, reset_day) VALUES (?,?,?,?)", [self.discord,self.channel, self.surprise_day.timestamp(), self.reset_day.timestamp()])
        self.id = res.lastrowid
        database.commit()
    
    def update_channel(self, database: Connection, channel: str):
        database.execute("UPDATE surprise_days SET channel = ? WHERE id = ?", (channel, self.id))
        database.commit()
        self.channel = channel
    
    def get_from_channel(database: Connection, channel: str) -> SurpriseDay | None:
        cur = database.cursor()
        res = cur.execute("""SELECT id, discord, channel, surprise_day, reset_day FROM surprise_days WHERE "channel"=?;""", [channel])
        res = res.fetchone()
        if res == None:
            return None
        id, discord, channel, surprise_day, reset_day = res
        return SurpriseDay(id, discord, channel, datetime.fromtimestamp(surprise_day), datetime.fromtimestamp(reset_day))

    def get_from_discord(database: Connection, discord: str) -> SurpriseDay | None:
        cur = database.cursor()
        res = cur.execute("""SELECT id, discord, channel, surprise_day, reset_day FROM surprise_days WHERE "discord"=?;""", [discord])
        res = res.fetchone()
        if res == None:
            return None
        id, discord, channel, surprise_day, reset_day = res
        return SurpriseDay(id, discord, channel, datetime.fromtimestamp(surprise_day), datetime.fromtimestamp(reset_day))

    def get_from_discord_or_default(database: Connection, discord: str) -> SurpriseDay:
        res = SurpriseDay.get_from_discord(database, discord)
        if res is not None:
            return res

        now = normalize_datetime(datetime.now())
        surprise_day = random_surprise_day(now)
        reset_day = now + timedelta(days=365)
        res = SurpriseDay(0, discord, None, surprise_day, reset_day)
        
        res.create(database)
        return res
    


    def __repr__(self) -> str:
        return "{} {} {} {}".format(self.id, self.discord, self.surprise_day, self.reset_day)

    def setup(database: Connection) -> None:
        database.execute("""CREATE TABLE IF NOT EXISTS "surprise_days" (
        "id"	INTEGER,
        "discord"	TEXT,
        "channel"	TEXT,
        "surprise_day"	INTEGER,
        "reset_day"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT)
        );""")
        database.commit()