
import os
import discord
from discord.ext import commands


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Zweryfikuj się",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="verification:verify"
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        if guild is None:
            return

        role_id = os.getenv("VERIFIED_ROLE_ID", "").strip()

        if not role_id.isdigit():
            await interaction.response.send_message(
                "Weryfikacja nie jest jeszcze skonfigurowana.",
                ephemeral=True
            )
            return

        role = guild.get_role(int(role_id))

        if role is None:
            await interaction.response.send_message(
                "Nie znaleziono roli weryfikacji. Sprawdź jej ID.",
                ephemeral=True
            )
            return

        member = interaction.user

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Nie udało się pobrać danych użytkownika.",
                ephemeral=True
            )
            return

        if role in member.roles:
            await interaction.response.send_message(
                "Masz już przyznaną rolę! ✅",
                ephemeral=True
            )
            return

        try:
            await member.add_roles(
                role,
                reason="Weryfikacja przez przycisk"
            )

            await interaction.response.send_message(
                "Pomyślnie się zweryfikowano! Miłego pobytu na serwerze. 🎉",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Bot nie ma uprawnień do nadania tej roli. "
                "Przenieś jego rolę wyżej w hierarchii.",
                ephemeral=True
            )


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(VerificationView())

    @commands.hybrid_command(
        name="weryfikacja",
        description="Wyślij panel weryfikacji"
    )
    @commands.has_permissions(administrator=True)
    async def verification_panel(self, ctx):
        embed = discord.Embed(
            title="✅ Weryfikacja",
            description=(
                "Aby uzyskać dostęp do serwera, kliknij przycisk "
                "**Zweryfikuj się** poniżej."
            ),
            color=discord.Color.green()
        )

        await ctx.send(
            embed=embed,
            view=VerificationView()
        )


async def setup(bot):
    await bot.add_cog(Verification(bot))
