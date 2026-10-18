
import discord
from discord.ext import commands


class SelfRoleSelect(discord.ui.Select):
    def __init__(self, roles):
        options = [
            discord.SelectOption(
                label=role.name[:100],
                value=str(role.id),
                description=f"Wybierz rolę: {role.name}"[:100]
            )
            for role in roles[:25]
        ]

        super().__init__(
            placeholder="Wybierz swoje role...",
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id="selfroles:select"
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(
            interaction.user, discord.Member
        ):
            return

        selected_ids = {int(value) for value in self.values}
        allowed_ids = {int(option.value) for option in self.options}

        # Nie pozwalaj menu nadać ról spoza jego listy.
        selected_ids &= allowed_ids

        selected_roles = [
            interaction.guild.get_role(role_id)
            for role_id in selected_ids
        ]
        selected_roles = [role for role in selected_roles if role]

        member = interaction.user

        try:
            for role in selected_roles:
                if role not in member.roles:
                    await member.add_roles(
                        role,
                        reason="Samodzielny wybór roli"
                    )

            # Role z listy, których użytkownik odznaczył, zostają zabrane.
            for option in self.options:
                role = interaction.guild.get_role(int(option.value))

                if role and role in member.roles and role.id not in selected_ids:
                    await member.remove_roles(
                        role,
                        reason="Odznaczenie roli w menu"
                    )

            await interaction.response.send_message(
                "Twoje role zostały zaktualizowane! 🎭",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Nie mogę nadać lub zabrać tych ról. "
                "Sprawdź uprawnienia i hierarchię ról bota.",
                ephemeral=True
            )


class SelfRoleView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=None)
        self.add_item(SelfRoleSelect(roles))


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="rolepanel",
        description="Utwórz panel wyboru własnych ról"
    )
    @commands.has_permissions(administrator=True)
    async def rolepanel(self, ctx, role1: discord.Role,
                        role2: discord.Role = None,
                        role3: discord.Role = None,
                        role4: discord.Role = None,
                        role5: discord.Role = None):
        roles = [
            role for role in
            [role1, role2, role3, role4, role5]
            if role is not None
        ]

        if len({role.id for role in roles}) != len(roles):
            await ctx.send("Nie wybieraj tej samej roli kilka razy.")
            return

        if ctx.guild and any(
            role.is_default() or role.managed for role in roles
        ):
            await ctx.send(
                "Nie można udostępniać roli @everyone "
                "ani ról zarządzanych przez integracje."
            )
            return

        embed = discord.Embed(
            title="🎭 Wybierz swoje role",
            description=(
                "Wybierz role z menu poniżej.\n"
                "Możesz zaznaczyć kilka naraz. "
                "Odznaczenie roli z tego panelu ją odbierze."
            ),
            color=discord.Color.blurple()
        )

        await ctx.send(
            embed=embed,
            view=SelfRoleView(roles)
        )


async def setup(bot):
    await bot.add_cog(Roles(bot))
