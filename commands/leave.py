import hikari
import lightbulb

from models.bot import SurpriseBot

plugin = lightbulb.Plugin(name="leave")


@plugin.command()
@lightbulb.app_command_permissions(hikari.Permissions.NONE, dm_enabled=False)
@lightbulb.command("leave", "Leave someone else's channel ;(")
@lightbulb.implements(lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context):
    assert ctx.member is not None
    # This could be handled by subclassing lightbulb.Context as well, but it works for now.
    assert isinstance(ctx.app, SurpriseBot)

    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)

    day = await ctx.app.db.fetch_day_by_channel(ctx.channel_id)
    if day is None:
        await ctx.respond("You are not in a celebratory channel!", flags=hikari.MessageFlag.EPHEMERAL)
        return

    assert day.channel is not None
    await ctx.app.rest.delete_permission_overwrite(hikari.Snowflake(day.channel), ctx.member)
    await ctx.respond("Successfully left channel!", flags=hikari.MessageFlag.EPHEMERAL)


def load(bot: SurpriseBot):
    bot.add_plugin(plugin)


def unload(bot: SurpriseBot):
    bot.remove_plugin(plugin)
