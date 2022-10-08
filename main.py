import os

import dotenv
import hikari

from models.bot import SurpriseBot

dotenv.load_dotenv()

TOKEN = os.getenv("TOKEN")
assert TOKEN is not None

CATEGORY = os.getenv("CATEGORY")
assert CATEGORY is not None
CATEGORY = hikari.Snowflake(CATEGORY)

GUILD = os.getenv("GUILD")
assert GUILD is not None
GUILD = hikari.Snowflake(GUILD)

bot = SurpriseBot(
    db_file="database.db",
    token=TOKEN,
    category=CATEGORY,
    default_enabled_guilds=(GUILD,),
    intents=hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.GUILD_MEMBERS,
)

bot.run()
