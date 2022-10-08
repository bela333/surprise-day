import datetime
import logging
import os
import typing as t

import aiosqlite
import hikari
import lightbulb
from lightbulb.ext import tasks

import utils
from models.database import Database

logger = logging.getLogger(__name__)


class SurpriseBot(lightbulb.BotApp):
    def __init__(self, db_file: str, category: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._db_file: str = os.path.join(self.path, db_file)
        self._db: t.Optional[Database] = None
        self._category: hikari.Snowflake = hikari.Snowflake(category)
        self.subscribe_listeners()
        tasks.load(self)

    @property
    def path(self) -> str:
        """The path of the directory the bot is running from."""
        return os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir))

    @property
    def db(self) -> Database:
        """The current database connection of the bot."""
        if db := self._db:
            return db
        raise hikari.ComponentStateConflictError("Database is not yet initialized.")

    @property
    def category(self) -> hikari.Snowflake:
        """The category ID of the surprise day channels the bot handles."""
        return self._category

    def subscribe_listeners(self) -> None:
        """Start all listeners located in this class."""
        self.subscribe(hikari.StartingEvent, self.on_starting)
        self.subscribe(hikari.StartedEvent, self.on_started)
        self.subscribe(hikari.StoppingEvent, self.on_stopping)
        self.subscribe(hikari.MemberCreateEvent, self.on_member_create)
        self.subscribe(hikari.MemberDeleteEvent, self.on_member_delete)

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        """Called once when the bot is starting up."""

        try:
            self._db = Database(await aiosqlite.connect(self._db_file))
        except Exception as e:
            logger.critical(f"Failed to initialize database: {e}.")
            await self.close()

        await self.db.create_schema()

        self.load_extensions_from(os.path.join(self.path, "commands"), must_exist=True)

    async def on_started(self, _: hikari.StartedEvent) -> None:
        """Called once when the bot has started up."""
        self.reset_surprisedays.start()

    async def on_stopping(self, _: hikari.StoppingEvent) -> None:
        """Called once when the bot is shutting down."""
        await self.db.close()

    async def on_member_create(self, event: hikari.MemberCreateEvent) -> None:
        """On new member join, generate a new surprise day channel."""

        day = await self.db.fetch_or_create_day(event.member)

        if not day.channel:  # Do not create a new channel if one already exists (should this even happen?).
            day.channel = await self.rest.create_guild_text_channel(
                event.guild_id,
                event.member.username,
                category=self.category,
                permission_overwrites=[
                    hikari.PermissionOverwrite(
                        id=event.guild_id,
                        type=hikari.PermissionOverwriteType.ROLE,
                        deny=hikari.Permissions.VIEW_CHANNEL,
                    )
                ],
            )
        channel_id = hikari.Snowflake(day.channel)

        day.message = await self.rest.create_message(
            channel_id,
            "{0}'s Surprise Day is on <t:{1}>, <t:{1}:R>".format(
                event.member.mention, int(day.surprise_day.timestamp())
            ),
        )

        await self.db.update_day(day)
        await self.rest.pin_message(channel_id, day.message.id)
        logger.info(f"Generated surprise day for: {event.member.id}")

    async def on_member_delete(self, event: hikari.MemberDeleteEvent) -> None:
        """On member leave, clear up the surprise day channel."""

        day = await self.db.fetch_day_by_user(event.user_id)
        if day is None or day.channel is None:
            return
        await self.rest.delete_channel(day.channel)
        day.message, day.channel = None, None

        await self.db.update_day(day)
        logger.info(f"Cleaned up surprise day channel for: {event.user_id}")

    @tasks.task(tasks.CronTrigger("0 0 * * *"))
    async def reset_surprisedays(self):
        logger.info("Resetting surprise days...")

        for day in await self.db.fetch_expired_days(datetime.datetime.now(datetime.timezone.utc)):
            if day.channel is None:
                # if channel is None, user probably left, so we clear their entry and continue
                await self.db.delete_day(day)
                continue

            day.surprise_day, day.reset_day = utils.generate_random_days()

            if day.message is not None:
                try:
                    await self.rest.delete_message(hikari.Snowflake(day.channel), hikari.Snowflake(day.message))
                except hikari.NotFoundError:
                    pass

            day.message = await self.rest.create_message(
                day.channel,
                "<@{0}>'s Surprise Day is on <t:{1}>, <t:{1}:R>".format(
                    hikari.Snowflake(day.user), int(day.surprise_day.timestamp())
                ),
            )
            await self.rest.pin_message(day.message.channel_id, day.message)

            await self.db.update_day(day)
