from __future__ import annotations

import datetime
import typing as t

import aiosqlite
import hikari

import utils
from models.surprise_day import SurpriseDay


class Database:
    __slots__: t.Sequence[str] = ("_connection",)

    def __init__(self, connection: aiosqlite.Connection) -> None:
        self._connection = connection

    @property
    def connection(self) -> aiosqlite.Connection:
        return self._connection

    async def create_day(
        self,
        user: hikari.SnowflakeishOr[hikari.PartialUser],
        message: t.Optional[hikari.SnowflakeishOr[hikari.PartialMessage]],
        channel: t.Optional[hikari.SnowflakeishOr[hikari.TextableChannel]],
        surprise_day: datetime.datetime,
        reset_day: datetime.datetime,
    ) -> SurpriseDay:
        """Create a new surprise day entry in the database.

        This will also generate a new ID for the day.

        Parameters
        ----------
        user: hikari.SnowflakeishOr[hikari.PartialUser]
            The user to create the day for.
        message: t.Optional[hikari.SnowflakeishOr[hikari.PartialMessage]]
            The message to associate with the day.
        channel: t.Optional[hikari.SnowflakeishOr[hikari.TextableChannel]]
            The channel to associate with the day.
        surprise_day: datetime.datetime
            The day the surprise will happen.
        reset_day: datetime.datetime
            The day surprise_day will reset.

        Returns
        -------
        SurpriseDay
            The newly created SurpriseDay.
        """

        cur = await self.connection.cursor()
        res = await cur.execute(
            "INSERT INTO surprise_days(discord, message, channel, surprise_day, reset_day) VALUES (?,?,?,?,?)",
            (
                str(hikari.Snowflake(user)),
                str(hikari.Snowflake(message)) if message is not None else None,
                str(hikari.Snowflake(channel)) if channel is not None else None,
                int(surprise_day.timestamp()),
                int(reset_day.timestamp()),
            ),
        )
        await self.connection.commit()

        return SurpriseDay(res.lastrowid, user, message, channel, surprise_day, reset_day)

    async def update_day(
        self,
        day: SurpriseDay,
    ) -> None:
        """Sync the state of the passed SurpriseDay to the database.

        Parameters
        ----------
        day: SurpriseDay
            The day to update.
        """

        cur = await self.connection.cursor()
        await cur.execute(
            "UPDATE surprise_days SET discord = ?, message = ?, channel = ?, surprise_day = ?, reset_day = ? WHERE id = ?",
            (day.serialize(with_id=True)),
        )
        await self.connection.commit()

    async def delete_day(
        self,
        day: SurpriseDay,
    ) -> None:
        """Delete a SurpriseDay entry from the database.

        Parameters
        ----------
        day: SurpriseDay
            The day to delete.
        """

        cur = await self.connection.cursor()
        await cur.execute(
            "DELETE FROM surprise_days WHERE id = ?",
            (day.id,),
        )
        await self.connection.commit()

    async def fetch_expired_days(self, date: datetime.datetime) -> t.Sequence[SurpriseDay]:
        """Fetch all days that have expired.

        Parameters
        ----------
        date: datetime.datetime
            The date to check expiration by.

        Returns
        -------
        Sequence[SurpriseDay]
            A list of expired days.
        """

        timestamp = int(date.timestamp())
        cur = await self.connection.cursor()
        res = await cur.execute(
            """SELECT id, discord, message, channel, surprise_day, reset_day FROM surprise_days WHERE reset_day < ?;""",
            (timestamp,),
        )
        return [SurpriseDay.from_row(tuple(row)) for row in await res.fetchall()]

    async def fetch_day_by_channel(
        self, channel: hikari.SnowflakeishOr[hikari.TextableChannel]
    ) -> t.Optional[SurpriseDay]:
        """Fetch a day by channel.

        Parameters
        ----------
        channel: hikari.SnowflakeishOr[hikari.TextableChannel]
            The channel that belongs to the surprise day.

        Returns
        -------
        Optional[SurpriseDay]
            The day that belongs to the channel, or None if it doesn't exist.
        """

        cur = await self.connection.cursor()
        channel_id = str(hikari.Snowflake(channel))

        res = await cur.execute("""SELECT * FROM surprise_days WHERE "channel"=?;""", (channel_id,))
        if row := await res.fetchone():
            return SurpriseDay.from_row(tuple(row))

    async def fetch_day_by_user(self, user: hikari.SnowflakeishOr[hikari.PartialUser]) -> t.Optional[SurpriseDay]:
        """Fetch a day by user.

        Parameters
        ----------
        user: hikari.SnowflakeishOr[hikari.PartialUser]
            The user that belongs to the surprise day.

        Returns
        -------
        Optional[SurpriseDay]
            The day that belongs to the user, or None if it doesn't exist.
        """
        user_id = str(hikari.Snowflake(user))

        cur = await self.connection.cursor()

        res = await cur.execute("""SELECT * FROM surprise_days WHERE "discord"=?;""", (user_id,))
        if row := await res.fetchone():
            return SurpriseDay.from_row(tuple(row))

    async def fetch_or_create_day(self, user: hikari.SnowflakeishOr[hikari.PartialUser]) -> SurpriseDay:
        """Get a surprise day from the database, or create a new one if it doesn't exist.

        Parameters
        ----------
        user: hikari.SnowflakeishOr[hikari.PartialUser]
            The user to get the day for.

        Returns
        -------
        SurpriseDay
            The day that belongs to the user, created if necessary.
        """
        if day := await self.fetch_day_by_user(user):
            return day

        surprise_day, reset_day = utils.generate_random_days()

        return await self.create_day(user, None, None, surprise_day, reset_day)

    async def create_schema(self) -> None:
        """Create the database schema if it doesn't exist already."""

        await self.connection.execute(
            """CREATE TABLE IF NOT EXISTS "surprise_days" (
                "id"	INTEGER NOT NULL UNIQUE,
                "discord"	TEXT NOT NULL UNIQUE,
                "message"	TEXT,
                "channel"	TEXT,
                "surprise_day"	INTEGER NOT NULL,
                "reset_day"	INTEGER NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT)
            );"""
        )
        await self.connection.commit()
