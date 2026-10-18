
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Zsynchronizowano {len(synced)} komend.")
    except Exception as e:
        print(f"Blad synchronizacji komend: {e}")


async def load_cogs():
    cogs = [
        "cogs.tickets",
        "cogs.verification",
        "cogs.roles",
        "cogs.welcome"
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"Zaladowano: {cog}")
        except Exception as e:
            print(f"Blad {cog}: {e}")


async def main():
    if not TOKEN:
        raise RuntimeError(
            "Brak DISCORD_TOKEN w zmiennych srodowiskowych!"
        )

    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
