
import os
import re
import discord
from discord.ext import commands


def get_staff_role_ids():
    names = [
        "TICKET_OWNER_ROLE_ID",
        "TICKET_COWNER_ROLE_ID",
        "TICKET_ADMIN_ROLE_ID",
        "TICKET_MOD_ROLE_ID",
    ]

    result = set()

    for name in names:
        value = os.getenv(name, "").strip()
        if value.isdigit() and int(value) != 0:
            result.add(int(value))

    return result


def is_staff(member):
    if not isinstance(member, discord.Member):
        return False

    staff_ids = get_staff_role_ids()

    return (
        member.guild_permissions.administrator
        or any(role.id in staff_ids for role in member.roles)
    )


class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Otwórz ticket",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="ticket:open"
    )
    async def open_ticket(self, interaction, button):
        guild = interaction.guild

        if guild is None:
            return

        category_id = os.getenv("TICKET_CATEGORY_ID", "").strip()

        if not category_id.isdigit():
            await interaction.response.send_message(
                "System ticketów nie jest skonfigurowany.",
                ephemeral=True
            )
            return

        category = guild.get_channel(int(category_id))

        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message(
                "Nie znaleziono kategorii ticketów. Sprawdź jej ID.",
                ephemeral=True
            )
            return

        for channel in category.text_channels:
            if channel.topic == f"ticket_owner:{interaction.user.id}":
                await interaction.response.send_message(
                    f"Masz już ticket: {channel.mention}",
                    ephemeral=True
                )
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            )
        }

        bot_member = guild.me

        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )

        staff_roles = []

        for role_id in get_staff_role_ids():
            role = guild.get_role(role_id)

            if role:
                staff_roles.append(role)
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

        safe_name = re.sub(
            r"[^a-z0-9-]",
            "-",
            interaction.user.name.lower()
        )[:20] or "uzytkownik"

        await interaction.response.defer(ephemeral=True)

        try:
            channel = await guild.create_text_channel(
                name=f"ticket-{safe_name}",
                category=category,
                topic=f"ticket_owner:{interaction.user.id}",
                overwrites=overwrites,
                reason="Utworzenie ticketu"
            )

            embed = discord.Embed(
                title="🎫 Ticket utworzony",
                description=(
                    f"Witaj {interaction.user.mention}!\n\n"
                    "Opisz swój problem, a administracja odpowie "
                    "tak szybko, jak to możliwe."
                ),
                color=discord.Color.blurple()
            )

            mentions = " ".join(role.mention for role in staff_roles)

            await channel.send(
                content=mentions or None,
                embed=embed,
                view=TicketControls()
            )

            await interaction.followup.send(
                f"Twój ticket został utworzony: {channel.mention}",
                ephemeral=True
            )

        except discord.HTTPException:
            await interaction.followup.send(
                "Nie udało się utworzyć ticketu. Sprawdź uprawnienia bota.",
                ephemeral=True
            )


class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Zamknij ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:close"
    )
    async def close_ticket(self, interaction, button):
        channel = interaction.channel
        guild = interaction.guild

        if not isinstance(channel, discord.TextChannel) or guild is None:
            return

        if not channel.topic or not channel.topic.startswith("ticket_owner:"):
            await interaction.response.send_message(
                "To nie jest ticket.",
                ephemeral=True
            )
            return

        owner_id = int(channel.topic.split(":")[1])

        if interaction.user.id != owner_id and not is_staff(interaction.user):
            await interaction.response.send_message(
                "Nie masz uprawnień do zamknięcia tego ticketu.",
                ephemeral=True
            )
            return

        owner = guild.get_member(owner_id)

        if owner:
            await channel.set_permissions(
                owner,
                view_channel=False,
                send_messages=False
            )

        await channel.edit(
            name=f"closed-{channel.name}"[:100]
        )

        await interaction.response.send_message(
            "🔒 Ticket został zamknięty."
        )

    @discord.ui.button(
        label="Otwórz ponownie",
        emoji="🔓",
        style=discord.ButtonStyle.success,
        custom_id="ticket:reopen"
    )
    async def reopen_ticket(self, interaction, button):
        channel = interaction.channel
        guild = interaction.guild

        if not isinstance(channel, discord.TextChannel) or guild is None:
            return

        if not channel.topic or not channel.topic.startswith("ticket_owner:"):
            await interaction.response.send_message(
                "To nie jest ticket.",
                ephemeral=True
            )
            return

        owner_id = int(channel.topic.split(":")[1])

        if not is_staff(interaction.user):
            await interaction.response.send_message(
                "Tylko administracja może ponownie otworzyć ticket.",
                ephemeral=True
            )
            return

        owner = guild.get_member(owner_id)

        if owner:
            await channel.set_permissions(
                owner,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            )

        new_name = channel.name

        if new_name.startswith("closed-"):
            new_name = new_name[7:]

        await channel.edit(name=new_name[:100])

        await interaction.response.send_message(
            "🔓 Ticket został ponownie otwarty."
        )


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(TicketPanel())
        self.bot.add_view(TicketControls())

    @commands.hybrid_command(
        name="ticketpanel",
        description="Wyślij panel ticketów"
    )
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx):
        embed = discord.Embed(
            title="🎫 Centrum pomocy",
            description=(
                "Potrzebujesz pomocy?\n"
                "Kliknij przycisk poniżej, aby utworzyć prywatny ticket."
            ),
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed, view=TicketPanel())


async def setup(bot):
    await bot.add_cog(Tickets(bot))
