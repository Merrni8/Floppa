
import re
import discord
from discord.ext import commands


ROLE_NAMES = {
    "Pro": "🦠・Pro",
    "Master": "🏆・Master",
    "Legenda": "🪬・Legenda",
    "Mityk": "👾・Mytic",
    "Diament": "💎・Diament",
    "Gold": "🪎・Gold",
    "Silver": "🪙・Silver",
    "Bronze": "💩・Bronze",
}

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


def find_emoji(guild, name):
    for emoji in guild.emojis:
        if emoji.name and emoji.name.casefold() == name.casefold():
            return emoji
    return None


class RoleButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"rankbutton:(?P<role_id>[0-9]+)"
):
    def __init__(self, role_id, label, emoji=None):
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
        return cls(
            int(match["role_id"]),
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

        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(
                    role,
                    reason="Klikniecie panelu rang"
                )
                message = f"Odebrano range: {role.name}"
            else:
                await interaction.user.add_roles(
                    role,
                    reason="Klikniecie panelu rang"
                )
                message = f"Nadano range: {role.name}"

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Bot nie moze nadac tej rangi. Sprawdz "
                "uprawnienie Zarzadzanie rolami i hierarchie rang.",
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

        for label, role in roles:
            emoji_name = EMOJI_NAMES[label]
            emoji = find_emoji(guild, emoji_name)

            self.add_item(
                RoleButton(role.id, label, emoji=emoji)
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

        roles = []
        missing = []

        for label, full_name in ROLE_NAMES.items():
            role = discord.utils.get(
                ctx.guild.roles,
                name=full_name
            )

            if role is None:
                missing.append(full_name)
            elif role.is_default() or role.managed:
                missing.append(full_name)
            else:
                roles.append((label, role))

        if missing:
            await ctx.send(
                "Nie znaleziono rang:\n" + "\n".join(missing)
            )
            return

        missing_emojis = []

        for emoji_name in EMOJI_NAMES.values():
            if find_emoji(ctx.guild, emoji_name) is None:
                missing_emojis.append(f":{emoji_name}:")

        embed = discord.Embed(
            title="🏆 Wybierz swoją rangę",
            description=(
                "Kliknij przycisk, aby otrzymać rangę.\n"
                "Kliknij go ponownie, aby ją odebrać.\n\n"
                "Możesz wybrać kilka rang."
            ),
            color=discord.Color.blurple()
        )

        if missing_emojis:
            embed.add_field(
                name="Brakujące emotki",
                value=(
                    "Nie znaleziono: "
                    + ", ".join(missing_emojis)
                    + ". Te przyciski będą bez własnej emotki."
                ),
                inline=False
            )

        await ctx.send(
            embed=embed,
            view=RolePanelView(ctx.guild, roles)
        )


async def setup(bot):
    await bot.add_cog(Roles(bot))
