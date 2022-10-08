from datetime import datetime
import utils
import hikari
import lightbulb
import sqlite3
import aiocron
from commands import leave, join

from database.surprise_day import SurpriseDay

database = sqlite3.connect("database.db")
SurpriseDay.setup(database)

bot = lightbulb.BotApp(token=utils.TOKEN, intents=hikari.Intents.GUILD_MEMBERS)

# Run `reset` job every day at midnight
@aiocron.crontab("0 0 * * *", start=False)
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

async def handle_join(member: hikari.Member, guild: hikari.SnowflakeishOr[hikari.PartialGuild]) -> None:
    guild = hikari.Snowflake(guild)
    day = SurpriseDay.get_from_discord_or_default(database, str(member.id))
    if day.channel is not None:
        # TODO: Cleanup channel
        pass
    channel = await bot.rest.create_guild_text_channel(guild, member.username, category=utils.CATEGORY)
    
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
        return
    await handle_join(event.member, event.guild_id)

@bot.listen()
async def on_leave(event: hikari.MemberDeleteEvent) -> None:
    if event.old_member is not None and event.old_member.is_bot:
        return
    await handle_leave(event.user_id, event.guild_id)

@bot.listen()
async def on_start(event: hikari.StartingEvent) -> None:
    # Start `reset` job
    reset_surpriseday.start()

# Register commands

join.register_command(database, bot)
leave.register_command(database, bot)

if utils.is_debug():
    @bot.command
    @lightbulb.command("forcejoin", "Simulate a 'join' event")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def forcejoin(ctx: lightbulb.Context):
        if ctx.member is None or ctx.guild_id is None: return
        await handle_join(ctx.member, ctx.guild_id)
        await ctx.respond("Done!", flags=hikari.MessageFlag.EPHEMERAL)
    
    @bot.command
    @lightbulb.command("forceleave", "Simulate a 'leave' event")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def forceleave(ctx: lightbulb.Context):
        if ctx.member is None or ctx.guild_id is None: return
        await handle_leave(ctx.member.id, ctx.guild_id)
        await ctx.respond("Done!", flags=hikari.MessageFlag.EPHEMERAL)

bot.run()
