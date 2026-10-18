
import os
import discord
from discord.ext import commands


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel_id = os.getenv("WELCOME_CHANNEL_ID")

        if not channel_id:
            print("Brak WELCOME_CHANNEL_ID w zmiennych Railway.")
            return

        channel = member.guild.get_channel(int(channel_id))

        if channel is None:
            print(f"Nie znaleziono kanalu powitalnego: {channel_id}")
            return

        embed = discord.Embed(
            title="👋 Witamy na serwerze!",
            description=(
                f"Cześć {member.mention}!\n"
                f"Jesteś naszym **{member.guild.member_count}** członkiem!"
            ),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel_id = os.getenv("GOODBYE_CHANNEL_ID")

        if not channel_id:
            print("Brak GOODBYE_CHANNEL_ID w zmiennych Railway.")
            return

        channel = member.guild.get_channel(int(channel_id))

        if channel is None:
            print(f"Nie znaleziono kanalu pozegnalnego: {channel_id}")
            return

        embed = discord.Embed(
            title="👋 Do zobaczenia!",
            description=f"**{member.display_name}** opuścił serwer.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
