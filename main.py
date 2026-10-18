
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


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
            print(f"Blad {cog}: {type(e).__name__}: {e}")


@bot.event
async def setup_hook():
    await load_cogs()

    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()

        print("Zsynchronizowane komendy:")
        for command in synced:
            print(f"- /{command.name}")

        print(f"Lacznie: {len(synced)}")

    except Exception as e:
        print(f"Blad synchronizacji: {type(e).__name__}: {e}")


@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")


async def main():
    if not TOKEN:
        raise RuntimeError(
            "Brak DISCORD_TOKEN w zmiennych srodowiskowych!"
        )

    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
