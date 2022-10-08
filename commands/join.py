import sqlite3
import hikari
import lightbulb

from database.surprise_day import SurpriseDay


def register_command(database: sqlite3.Connection, bot: lightbulb.BotApp):
    @bot.command()
    @lightbulb.option("user", "User", hikari.User)
    @lightbulb.command("join", "Join someone else's celebration")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def join(ctx: lightbulb.Context):
        if ctx.member is None:
            await ctx.respond("Oops", flags=hikari.MessageFlag.EPHEMERAL)
            return
        if ctx.options.user is None:
            await ctx.respond("You need to specify a user", flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        user = hikari.Snowflake(ctx.options.user)
        if user == ctx.member.id:
            await ctx.respond("You can't join your own channel", flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        day = SurpriseDay.get_from_discord(database, str(user))
        if day is None or day.channel is None:
            await ctx.respond("This user does not have a celebratory channel", flags=hikari.MessageFlag.EPHEMERAL)
            return

        await bot.rest.edit_permission_overwrite(hikari.Snowflake(day.channel), ctx.member.id, target_type=hikari.PermissionOverwriteType.MEMBER, allow=hikari.Permissions.VIEW_CHANNEL)

        await ctx.respond("Joined!", flags=hikari.MessageFlag.EPHEMERAL)

        