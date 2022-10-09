from __future__ import annotations

import datetime
import typing as t

import attr
import hikari


@attr.define()
class SurpriseDay:
    """A model representing a user's surprise day. This class is not supposed to be directly instantiated, instead use Database.create_day() or SurpriseDay.from_row()."""

    id: int = attr.field()
    """Entry ID"""

    user: hikari.SnowflakeishOr[hikari.PartialUser] = attr.field()
    """The user this surprise day belongs to."""

    message: t.Optional[hikari.SnowflakeishOr[hikari.PartialMessage]] = attr.field()
    """The message ID of the surprise day message. May be None if the user left the guild."""

    channel: t.Optional[hikari.SnowflakeishOr[hikari.TextableChannel]] = attr.field()
    """The channel ID of the surprise day channel belonging to this user. May be None if the user left the guild."""

    surprise_day: datetime.datetime = attr.field()
    """The date and time of the surprise day."""

    reset_day: datetime.datetime = attr.field()
    """The date and time of the reset day, at this date a new surprise day is generated."""

    @classmethod
    def from_row(cls, row: t.Tuple[int, str, t.Optional[str], t.Optional[str], int, int]) -> SurpriseDay:
        """Create a SurpriseDay object from a database row.

        Parameters
        ----------
        row: t.Tuple[int, str, t.Optional[str], t.Optional[str], int, int]
            A database row.

        Returns
        -------
        SurpriseDay
            A SurpriseDay object.
        """

        return cls(
            id=row[0],
            user=hikari.Snowflake(row[1]),
            message=hikari.Snowflake(row[2]) if row[2] is not None else None,
            channel=hikari.Snowflake(row[3]) if row[3] is not None else None,
            surprise_day=datetime.datetime.fromtimestamp(row[4]),
            reset_day=datetime.datetime.fromtimestamp(row[5]),
        )

    def serialize(
        self, with_id: bool = False
    ) -> t.Tuple[str, t.Optional[str], t.Optional[str], int, int] | t.Tuple[
        str, t.Optional[str], t.Optional[str], int, int, int
    ]:
        """Serialize this object into a tuple representing a row for easy database insertion.

        Parameters
        ----------
        with_id: bool
            Whether to include the  entry ID in the tuple at the end. Defaults to False.

        Returns
        -------
        t.Tuple[str, t.Optional[str], t.Optional[str], int, int] | t.Tuple[str, t.Optional[str], t.Optional[str], int, int, int]
            A tuple representing a row for easy database insertion.
        """

        if with_id:
            return (
                str(hikari.Snowflake(self.user)),
                str(hikari.Snowflake(self.message)) if self.message is not None else None,
                str(hikari.Snowflake(self.channel)) if self.channel is not None else None,
                int(self.surprise_day.timestamp()),
                int(self.reset_day.timestamp()),
                self.id,
            )

        return (
            str(hikari.Snowflake(self.user)),
            str(hikari.Snowflake(self.message)) if self.message is not None else None,
            str(hikari.Snowflake(self.channel)) if self.channel is not None else None,
            int(self.surprise_day.timestamp()),
            int(self.reset_day.timestamp()),
        )
