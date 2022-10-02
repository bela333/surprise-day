from dotenv import load_dotenv
import hikari
import os
import sqlite3

from database.surprise_day import SurpriseDay, random_surprise_day

load_dotenv()
database = sqlite3.connect("database.db")

def setup():
    SurpriseDay.setup(database)
    print(SurpriseDay.get_from_discord_or_default(database, "80651592872759296"))


bot = hikari.GatewayBot(token=os.getenv("TOKEN"))

setup()
database.close()