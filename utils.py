from dotenv import load_dotenv
import os
import hikari
load_dotenv()

TOKEN = os.getenv("TOKEN")
assert TOKEN is not None
TOKEN = TOKEN

CATEGORY = os.getenv("CATEGORY")
assert CATEGORY is not None
CATEGORY = hikari.Snowflake(CATEGORY)

GUILD = os.getenv("GUILD")
assert GUILD is not None
GUILD = hikari.Snowflake(GUILD)


def is_debug() -> bool:
    d = os.getenv("DEBUG")
    return d == "1"