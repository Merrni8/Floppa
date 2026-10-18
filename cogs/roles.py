
import discord
from discord.ext import commands
from typing import Optional


class RoleButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"selfrole:(?P<role_id>[0-9]+)"
):
    def __init__(self, role_id: int, label: str):
        self.role_id = role_id

        button = discord.ui.Button(
            label=label[:80],
            style=discord.ButtonStyle.secondary,
            custom_id=f"selfrole:{role_id}"
        )

        super().__init__(button)

    @classmethod
    async def from_custom_id(
        cls,
        interaction: discord.Interaction,
        item: discord.ui.Button,
        match
    ):
        role_id = int(match["role_id"])

        role = (
            interaction.guild.get_role(role_id)
            if interaction.guild
            else None
        )

        label = role.name if role else "Niedostepna rola"

        return cls(role_id, label)

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
                    reason="Uzytkownik odznaczyl range"
                )
                message = f"Odebrano range: **{role.name}**"
            else:
                await member.add_roles(
                    role,
                    reason="Uzytkownik wybral range"
                )
                message = f"Nadano range: **{role.name}**"

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Bot nie moze zmienic tej rangi. Sprawdz "
                "uprawnienie Zarzadzanie rolami oraz to, "
                "czy najwyzsza rola bota jest wyzej "
                "od rangi do nadania.",
                ephemeral=True
            )

        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Wystapil blad Discorda. Sprobuj ponownie.",
                    ephemeral=True
                )


class RolePanelView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=None)

        for role in roles:
            self.add_item(RoleButton(role.id, role.name))


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_dynamic_items(RoleButton)

    async def cog_unload(self):
        self.bot.remove_dynamic_items(RoleButton)

    @commands.hybrid_command(
        name="rolepanel",
        description="Utworz panel przyciskow do wyboru rang"
    )
    @commands.has_permissions(administrator=True)
    async def rolepanel(
        self,
        ctx,
        role1: discord.Role,
        role2: Optional[discord.Role] = None,
        role3: Optional[discord.Role] = None,
        role4: Optional[discord.Role] = None,
        role5: Optional[discord.Role] = None,
        role6: Optional[discord.Role] = None,
        role7: Optional[discord.Role] = None,
        role8: Optional[discord.Role] = None,
        role9: Optional[discord.Role] = None,
        role10: Optional[discord.Role] = None
    ):
        if ctx.guild is None:
            await ctx.send(
                "Tej komendy uzywaj na serwerze."
            )
            return

        roles = [
            role for role in [
                role1, role2, role3, role4, role5,
                role6, role7, role8, role9, role10
            ]
            if role is not None
        ]

        unique_roles = {role.id for role in roles}

        if len(unique_roles) != len(roles):
            await ctx.send(
                "Nie wybieraj tej samej rangi kilka razy."
            )
            return

        for role in roles:
            if role.is_default() or role.managed:
                await ctx.send(
                    f"Rangi **{role.name}** nie mozna "
                    "udostepnic w tym panelu."
                )
                return

        embed = discord.Embed(
            title="🎭 Wybierz swoje rangi",
            description=(
                "Kliknij przycisk, aby otrzymac range.\n"
                "Kliknij go ponownie, aby ja odebrac.\n\n"
                "Mozesz wybrac kilka rang."
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="Panel rang • Wybieraj, co Ci odpowiada"
        )

        await ctx.send(
            embed=embed,
            view=RolePanelView(roles)
        )


async def setup(bot):
    await bot.add_cog(Roles(bot))
