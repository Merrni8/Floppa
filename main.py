
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


COGS = [
    "cogs.tickets",
    "cogs.verification",
    "cogs.roles",
    "cogs.welcome",
]


class CommunityBot(commands.Bot):
    async def setup_hook(self):
        # Zaladuj wszystkie moduly
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"Zaladowano: {cog}")
            except Exception as e:
                print(
                    f"Blad {cog}: "
                    f"{type(e).__name__}: {e}"
                )

        # Synchronizuj komendy
        try:
            if GUILD_ID:
                guild = discord.Object(id=int(GUILD_ID))

                # Skopiuj komendy do wybranego serwera
                self.tree.copy_global_to(guild=guild)

                # Usun stare komendy globalne Discorda
                self.tree.clear_commands(guild=None)
                await self.tree.sync()

                # Zostaw komendy na naszym serwerze
                synced = await self.tree.sync(guild=guild)
            else:
                print(
                    "UWAGA: Brak GUILD_ID. "
                    "Synchronizuje komendy globalnie."
                )
                synced = await self.tree.sync()

            print("Zsynchronizowane komendy:")
            for command in synced:
                print(f"- /{command.name}")

            print(f"Lacznie: {len(synced)}")

        except Exception as e:
            print(
                f"Blad synchronizacji: "
                f"{type(e).__name__}: {e}"
            )


bot = CommunityBot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")


async def main():
    if not TOKEN:
        raise RuntimeError(
            "Brak DISCORD_TOKEN w zmiennych Railway!"
        )

    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
