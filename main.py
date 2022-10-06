from datetime import datetime
from dotenv import load_dotenv
import hikari
import os
import sqlite3
import aiocron

from database.surprise_day import SurpriseDay


load_dotenv()

TOKEN = os.getenv("TOKEN")
assert TOKEN is not None

CATEGORY = os.getenv("CATEGORY")
assert CATEGORY is not None
CATEGORY = hikari.Snowflake(CATEGORY)

GUILD = os.getenv("GUILD")
assert GUILD is not None
GUILD = hikari.Snowflake(GUILD)


def is_debug() -> bool:
    d = os.getenv("DEBUG")
    return d == "1"


database = sqlite3.connect("database.db")


def setup():
    SurpriseDay.setup(database)


bot = hikari.GatewayBot(token=TOKEN, intents=hikari.Intents.GUILD_MEMBERS)

setup()


#@aiocron.crontab("* * * * *", start=False)  # Every minute (for debugging)
@aiocron.crontab("0 0 * * *", start=False) # Every day
async def reset_surpriseday():
    for day in SurpriseDay.get_expired(database, datetime.now()):
        if day.channel is None:
            continue
        surprise_day, reset_day = SurpriseDay.generate_surpriseday_and_resetday()
        day.update_surprise_day(database, surprise_day)
        day.update_reset_day(database, reset_day)
        msg = await bot.rest.create_message(
            hikari.Snowflake(day.channel),
            "<@{0}>'s Surprise Day is on <t:{1}>, <t:{1}:R>".format(day.discord, int(day.surprise_day.timestamp())),
        )
        await bot.rest.pin_message(msg.channel_id, msg)
        if day.message is not None:
            try:
                await bot.rest.delete_message(hikari.Snowflake(day.channel), hikari.Snowflake(day.message))
            except Exception:
                pass
        day.update_message(database, str(msg.id))


@bot.listen()
async def register_commands(event: hikari.StartingEvent) -> None:
    application = await bot.rest.fetch_application()

    commands = [
        bot.rest.slash_command_builder("join", "Join in someone else's celebration!").add_option(
            hikari.CommandOption(type=hikari.OptionType.USER, name="user", description="User", is_required=True)
        ),
        bot.rest.slash_command_builder("leave", "Leave someone else's channel ;("),
    ]
    debug_commands = [
        bot.rest.slash_command_builder("forcejoin", 'Runs the "on_join" event'),
        bot.rest.slash_command_builder("forceleave", 'Runs the "on_leave" event'),
    ]

    if is_debug():
        commands.extend(debug_commands)

    await bot.rest.set_application_commands(application=application.id, commands=commands, guild=GUILD)
    reset_surpriseday.start()


@bot.listen()
async def handle_interactions(event: hikari.InteractionCreateEvent) -> None:
    if not isinstance(event.interaction, hikari.CommandInteraction):
        return

    if is_debug():
        if event.interaction.command_name == "forcejoin":
            if event.interaction.member is None or event.interaction.guild_id is None:
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE, "Oops!", flags=hikari.MessageFlag.EPHEMERAL
                )
                return
            await handle_join(event.interaction.member, event.interaction.guild_id)
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE, "Good!", flags=hikari.MessageFlag.EPHEMERAL
            )
        if event.interaction.command_name == "forceleave":
            if event.interaction.member is None or event.interaction.guild_id is None:
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE, "Oops!", flags=hikari.MessageFlag.EPHEMERAL
                )
                return
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE, "Good!", flags=hikari.MessageFlag.EPHEMERAL
            )
            await handle_leave(event.interaction.member.id, event.interaction.guild_id)
    if event.interaction.command_name == "join":
        if (
            event.interaction.options is None
            or len(event.interaction.options) < 1
            or event.interaction.member is None
        ):
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE, "Oops!", flags=hikari.MessageFlag.EPHEMERAL
            )
            return
        userid = event.interaction.options[0].value
        if userid != event.interaction.member.id:
            day = SurpriseDay.get_from_discord(database, str(userid))
            if day is None or day.channel is None:
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE, "Unknown error", flags=hikari.MessageFlag.EPHEMERAL
                )
                return
            channel = await bot.rest.fetch_channel(hikari.Snowflake(day.channel))
            if channel is None or not isinstance(channel, hikari.GuildTextChannel):
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_CREATE, "Oops", flags=hikari.MessageFlag.EPHEMERAL
                )
                return
            await channel.edit_overwrite(
                event.interaction.member.id,
                target_type=hikari.PermissionOverwriteType.MEMBER,
                allow=hikari.Permissions.VIEW_CHANNEL,
            )
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE, "Joined!!", flags=hikari.MessageFlag.EPHEMERAL
            )
        else:
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE, "You can't choose yourself", flags=hikari.MessageFlag.EPHEMERAL
            )
    if event.interaction.command_name == "leave":
        if event.interaction.member is None:
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE, "Oops", flags=hikari.MessageFlag.EPHEMERAL
            )
            return
        day = SurpriseDay.get_from_channel(database, str(event.interaction.channel_id))
        if day is None:
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE,
                "You are not in a celebratory channel",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            return
        assert day.channel is not None
        channel = await bot.rest.fetch_channel(hikari.Snowflake(day.channel))
        if channel is None or not isinstance(channel, hikari.GuildTextChannel):
            await event.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE, "Oops", flags=hikari.MessageFlag.EPHEMERAL
            )
            return
        await channel.remove_overwrite(event.interaction.member.id)
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE, "Successfully left", flags=hikari.MessageFlag.EPHEMERAL
        )


async def handle_join(member: hikari.Member, guild: hikari.SnowflakeishOr[hikari.PartialGuild]) -> None:
    guild = hikari.Snowflake(guild)
    day = SurpriseDay.get_from_discord_or_default(database, str(member.id))
    if day.channel is not None:
        # TODO: Cleanup channel
        pass
    channel = await bot.rest.create_guild_text_channel(guild, member.username, category=CATEGORY)
    
    await channel.edit_overwrite(
        guild, deny=hikari.Permissions.VIEW_CHANNEL, target_type=hikari.PermissionOverwriteType.ROLE
    )
    day.update_channel(database, str(channel.id))

    msg = await channel.send(
        "<@{0}>'s Surprise Day is on <t:{1}>, <t:{1}:R>".format(member.id, int(day.surprise_day.timestamp()))
    )
    day.update_message(database, str(msg.id))
    await channel.pin_message(msg.id)


async def handle_leave(user_id: hikari.Snowflake, guild: hikari.SnowflakeishOr[hikari.PartialGuild]) -> None:
    guild = hikari.Snowflake(guild)
    day = SurpriseDay.get_from_discord(database, str(user_id))
    if day is None or day.channel is None:
        return
    await bot.rest.delete_channel(hikari.Snowflake(day.channel))
    day.update_channel(database, None)
    day.update_message(database, None)


@bot.listen()
async def on_join(event: hikari.MemberCreateEvent) -> None:
    if event.member.is_bot:
        # Skip bots
        return
    # TODO: Cached value might be None
    await handle_join(event.member, event.guild_id)


@bot.listen()
async def on_leave(event: hikari.MemberDeleteEvent) -> None:
    if event.old_member is not None and event.old_member.is_bot:
        return
    # TODO: Cached value might be None
    await handle_leave(event.user_id, event.guild_id)


bot.run()
