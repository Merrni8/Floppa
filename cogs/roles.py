
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


def normalize(text):
    return " ".join(text.casefold().split())


def find_role(guild, wanted_name):
    wanted = normalize(wanted_name)

    for role in guild.roles:
        if normalize(role.name) == wanted:
            return role

    return None


def find_emoji(guild, wanted_name):
    for emoji in guild.emojis:
        if emoji.name and emoji.name.casefold() == wanted_name.casefold():
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
    async def from_custom_id(cls, interaction, item, match):
        role_id = int(match["role_id"])
        return cls(
            role_id,
            item.label or "Ranga",
            item.emoji
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild

        if guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            await interaction.response.send_message(
                "Uzyj tego przycisku na serwerze.",
                ephemeral=True
            )
            return

        role = guild.get_role(self.role_id)

        if role is None:
            await interaction.response.send_message(
                "Ta ranga juz nie istnieje.",
                ephemeral=True
            )
            return

        member = interaction.user

        try:
            if role in member.roles:
                await member.remove_roles(
                    role,
                    reason="Uzytkownik kliknal panel rang"
                )
                message = f"Odebrano range {role.name}."
            else:
                await member.add_roles(
                    role,
                    reason="Uzytkownik kliknal panel rang"
                )
                message = f"Nadano range {role.name}."

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Bot nie moze nadac tej rangi. Sprawdz "
                "uprawnienie Zarzadzanie rolami oraz hierarchie rang.",
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
            emoji_name = EMOJI_NAMES[role.name]
            emoji = find_emoji(guild, emoji_name)

            self.add_item(
                RoleButton(role.id, role.name, emoji=emoji)
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
        description="Utworz panel rang z emotkami"
    )
    @commands.has_permissions(administrator=True)
    async def rolepanel(self, ctx):
        if ctx.guild is None:
            await ctx.send("Uzyj tej komendy na serwerze.")
            return

        roles_by_name = {
            normalize(role.name): role
            for role in ctx.guild.roles
        }

        roles = []
        missing_roles = []

        for name in ROLE_NAMES:
            role = roles_by_name.get(normalize(name))

            if role is None:
                missing_roles.append(name)
            elif role.is_default() or role.managed:
                missing_roles.append(name)
            else:
                roles.append(role)

        if missing_roles:
            all_names = [
                role.name for role in ctx.guild.roles
                if not role.is_default()
            ]

            await ctx.send(
                "Nie znalazlem rang: "
                + ", ".join(missing_roles)
                + "\nNazwy rang widoczne dla bota: "
                + (", ".join(all_names) if all_names else "brak")
            )
            return

        missing_emojis = [
            f":{emoji_name}:"
            for emoji_name in EMOJI_NAMES.values()
            if find_emoji(ctx.guild, emoji_name) is None
        ]

        embed = discord.Embed(
            title="🏆 Wybierz swoja range",
            description=(
                "Kliknij przycisk, aby otrzymac range.\n"
                "Kliknij go ponownie, aby ja odebrac."
            ),
            color=discord.Color.blurple()
        )

        if missing_emojis:
            embed.add_field(
                name="Brakujace emotki",
                value=(
                    "Nie znaleziono: "
                    + ", ".join(missing_emojis)
                    + ". Sprawdz nazwy emotek na serwerze."
                ),
                inline=False
            )

        await ctx.send(
            embed=embed,
            view=RolePanelView(ctx.guild, roles)
        )


async def setup(bot):
    await bot.add_cog(Roles(bot))
