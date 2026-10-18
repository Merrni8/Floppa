import discord
from discord.ext import commands


class SelfRoleSelect(discord.ui.Select):
    def __init__(self, roles, menu_number):
        self.role_ids = {role.id for role in roles}

        options = [
            discord.SelectOption(
                label=role.name[:100],
                value=str(role.id),
                description=f"Wybierz rolę: {role.name}"[:100]
            )
            for role in roles
        ]

        super().__init__(
            placeholder=f"Wybierz role ({menu_number})...",
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id=f"selfroles:select:{menu_number}"
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(
            interaction.user, discord.Member
        ):
            return

        selected_ids = {int(value) for value in self.values}
        member = interaction.user

        roles = [
            interaction.guild.get_role(role_id)
            for role_id in self.role_ids
        ]
        roles = [role for role in roles if role is not None]

        to_add = [
            role for role in roles
            if role.id in selected_ids and role not in member.roles
        ]
        to_remove = [
            role for role in roles
            if role.id not in selected_ids and role in member.roles
        ]

        try:
            if to_add:
                await member.add_roles(
                    *to_add, reason="Samodzielny wybór roli"
                )

            if to_remove:
                await member.remove_roles(
                    *to_remove, reason="Odznaczenie roli w panelu"
                )

            await interaction.response.send_message(
                "Twoje role zostały zaktualizowane! 🎭",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Nie mogę zmienić tych ról. Sprawdź uprawnienia "
                "Manage Roles oraz hierarchię ról bota.",
                ephemeral=True
            )

        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Discord zwrócił błąd podczas zmiany ról. "
                    "Spróbuj ponownie.",
                    ephemeral=True
                )


class SelfRoleView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=None)

        for index in range(0, len(roles), 25):
            chunk = roles[index:index + 25]
            menu_number = index // 25 + 1
            self.add_item(SelfRoleSelect(chunk, menu_number))


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="rolepanel",
        description="Utwórz panel wyboru własnych ról"
    )
    @commands.has_permissions(administrator=True)
    async def rolepanel(self, ctx, role_ids: str):
        if ctx.guild is None:
            await ctx.send("Tej komendy używaj na serwerze.")
            return

        try:
            ids = [
                int(value.strip())
                for value in role_ids.replace(" ", "").split(",")
                if value.strip()
            ]
        except ValueError:
            await ctx.send(
                "Podaj poprawne ID rang oddzielone przecinkami."
            )
            return

        if not ids:
            await ctx.send("Nie podano żadnych rang.")
            return

        if len(ids) != len(set(ids)):
            await ctx.send("Nie podawaj tej samej rangi dwa razy.")
            return

        if len(ids) > 125:
            await ctx.send(
                "Możesz dodać maksymalnie 125 rang do jednego panelu."
            )
            return

        roles = []
        for role_id in ids:
            role = ctx.guild.get_role(role_id)

            if role is None:
                await ctx.send(
                    f"Nie znaleziono rangi o ID `{role_id}`."
                )
                return

            if role.is_default() or role.managed:
                await ctx.send(
                    f"Rangi {role.name} nie można udostępnić "
                    "w panelu."
                )
                return

            roles.append(role)

        embed = discord.Embed(
            title="🎭 Wybierz swoje role",
            description=(
                "Wybierz role z menu poniżej.\n"
                "Możesz korzystać z kilku list. "
                "Odznaczenie roli w danej liście ją odbierze."
            ),
            color=discord.Color.blurple()
        )

        await ctx.send(
            embed=embed,
            view=SelfRoleView(roles)
        )


async def setup(bot):
    await bot.add_cog(Roles(bot))u
