import hikari
import lightbulb

from models.bot import SurpriseBot

plugin = lightbulb.Plugin(name="join")


@plugin.command()
@lightbulb.app_command_permissions(hikari.Permissions.NONE, dm_enabled=False)
@lightbulb.option("user", "User", hikari.User)
@lightbulb.command("join", "Join someone else's surprise day!", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.SlashContext, user: hikari.User) -> None:
    assert ctx.member is not None
    # This could be handled by subclassing lightbulb.Context as well, but it works for now.
    assert isinstance(ctx.app, SurpriseBot)

    if user.id == ctx.member.id:
        await ctx.respond("You can't join your own channel!", flags=hikari.MessageFlag.EPHEMERAL)
        return

    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)

    day = await ctx.app.db.fetch_day_by_user(user)
    if day is None or day.channel is None:
        await ctx.respond(
            "This user does not have a celebratory channel, or they are not a member of this server!",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    await ctx.app.rest.edit_permission_overwrites(
        hikari.Snowflake(day.channel),
        ctx.member.id,
        target_type=hikari.PermissionOverwriteType.MEMBER,
        allow=hikari.Permissions.VIEW_CHANNEL,
    )

    await ctx.respond(f"Joined {user.mention}'s surprise channel!", flags=hikari.MessageFlag.EPHEMERAL)


def load(bot: SurpriseBot):
    bot.add_plugin(plugin)


def unload(bot: SurpriseBot):
    bot.remove_plugin(plugin)
