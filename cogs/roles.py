
import re
import discord
from discord.ext import commands


ROLE_NAMES = [
    "Pro",
    "Master",
    "Legenda",
    "Mityk",
    "Diament",
    "Gold",
    "Silver",
    "Bronze",
]

EMOJI_NAMES = {
    "Pro": "prorank",
    "Master": "master",
    "Legenda": "legenda",
    "Mityk": "mityk",
    "Diament": "diament",
    "Gold": "gold",
    "Silver": "silver",
    "Bronze": "bronze",
}


def find_emoji(guild, emoji_name):
    for emoji in guild.emojis:
        if emoji.name.lower() == emoji_name.lower():
            return emoji
    return None


class RoleButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"rankbutton:(?P<role_id>[0-9]+)"
):
    def __init__(self, role_id: int, label: str, emoji=None):
        self.role_id = role_id

        button = discord.ui.Button(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"rankbutton:{role_id}",
            emoji=emoji
        )

        super().__init__(button)

    @classmethod
    async def from_custom_id(
        cls,
        interaction: discord.Interaction,
        item: discord.ui.Button,
        match: re.Match
    ):
        role_id = int(match["role_id"])
        label = item.label or "Ranga"
        emoji = item.emoji
        return cls(role_id, label, emoji)

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Ta funkcja dziala tylko na serwerze.",
                ephemeral=True
            )
            return

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Nie udalo sie rozpoznac uzytkownika.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(self.role_id)

        if role is None:
            await interaction.response.send_message(
                "Ta ranga juz nie istnieje.",
                ephemeral=True
            )
            return

        if role.is_default() or role.managed:
            await interaction.response.send_message(
                "Nie mozna nadac tej rangi.",
                ephemeral=True
            )
            return

        member = interaction.user

        try:
            if role in member.roles:
                await member.remove_roles(
                    role,
                    reason="Uzytkownik kliknal przycisk rangi"
                )
                message = f"Odebrano range **{role.name}**."
            else:
                await member.add_roles(
                    role,
                    reason="Uzytkownik kliknal przycisk rangi"
                )
                message = f"Nadano range **{role.name}**."

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Bot nie moze zmienic tej rangi. Sprawdz "
                "uprawnienie Zarzadzanie rolami i hierarchie rol.",
                ephemeral=True
            )

        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Blad Discorda. Sprobuj ponownie.",
                    ephemeral=True
                )


class RolePanelView(discord.ui.View):
    def __init__(self, guild, roles):
        super().__init__(timeout=None)

        for role in roles:
            emoji_name = EMOJI_NAMES.get(role.name)
            emoji = (
                find_emoji(guild, emoji_name)
                if emoji_name
                else None
            )

            self.add_item(
                RoleButton(
                    role.id,
                    role.name,
                    emoji=emoji
                )
            )


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_dynamic_items(RoleButton)

    async def cog_unload(self):
        self.bot.remove_dynamic_items(RoleButton)

    @commands.hybrid_command(
        name="rolepanel",
        description="Utworz panel przyciskow rang"
    )
    @commands.has_permissions(administrator=True)
    async def rolepanel(self, ctx):
        if ctx.guild is None:
            await ctx.send(
                "Tej komendy uzywaj na swoim serwerze."
            )
            return

        server_roles = {
            role.name.casefold(): role
            for role in ctx.guild.roles
        }

        roles = []
        missing_roles = []

        for name in ROLE_NAMES:
            role = server_roles.get(name.casefold())

            if role is None:
                missing_roles.append(name)
            elif role.is_default() or role.managed:
                missing_roles.append(name)
            else:
                roles.append(role)

        if missing_roles:
            await ctx.send(
                "Nie znalazlem tych rang na serwerze:\n"
                + ", ".join(missing_roles)
                + "\nSprawdz dokladne nazwy rang."
            )
            return

        missing_emojis = []

        for role_name, emoji_name in EMOJI_NAMES.items():
            if find_emoji(ctx.guild, emoji_name) is None:
                missing_emojis.append(f":{emoji_name}:")

        embed = discord.Embed(
            title="🏆 Wybierz swoja range",
            description=(
                "Kliknij przycisk, aby otrzymac range.\n"
                "Kliknij ponownie, aby ja odebrac.\n\n"
                "Mozesz wybrac jedna lub kilka rang."
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="Panel rang • Wybieraj swoje rangi"
        )

        if missing_emojis:
            embed.add_field(
                name="Brakujace emotki",
                value=(
                    "Nie znaleziono: "
                    + ", ".join(missing_emojis)
                    + "\nTe przyciski beda bez wlasnej emotki."
                ),
                inline=False
            )

        await ctx.send(
            embed=embed,
            view=RolePanelView(ctx.guild, roles)
        )


async def setup(bot):
    await bot.add_cog(Roles(bot))
