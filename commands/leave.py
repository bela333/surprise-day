import aiosqlite
import hikari
import lightbulb

from database.surprise_day import SurpriseDay


def register_command(database: aiosqlite.core.Connection, bot: lightbulb.BotApp):
    @bot.command()
    @lightbulb.command("leave", "Leave someone else's channel ;(")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def leave(ctx: lightbulb.Context):
        if ctx.member is None:
            await ctx.respond("Oops", flags=hikari.MessageFlag.EPHEMERAL)
            return
        day = await SurpriseDay.get_from_channel(database, str(ctx.channel_id))
        if day is None:
            await ctx.respond("You are not in a celebratory channel", flags=hikari.MessageFlag.EPHEMERAL)
            return
        assert day.channel is not None
        await bot.rest.delete_permission_overwrite(hikari.Snowflake(day.channel), ctx.member)
        await ctx.respond("Successfully left channel", flags=hikari.MessageFlag.EPHEMERAL)