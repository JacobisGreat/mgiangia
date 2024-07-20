import discord
from discord.ext import commands
from discord import app_commands

# List of user IDs who are allowed to run the setup command
AUTHORIZED_USERS = [
    1091118146519322674,  # Replace with actual user IDs
    987654321098765432
]

class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Send an embed message to a specific channel.")
    @app_commands.describe(channel_id="The ID of the channel to send the embed to")
    async def setup(self, interaction: discord.Interaction, channel_id: str):
        if interaction.user.id not in AUTHORIZED_USERS:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return

        embed = discord.Embed(
            description="**__Fees:__**\nDeals $250+: 1%\nDeals under $250: $2\n__Deals under $50 are **FREE**__\n\nPress the dropdown below to select & initiate a deal involving either **Bitcoin, Ethereum, or Litecoin.**",
            color=65288
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1262514900815581304/1264054838103117864/image.jpg?ex=669c7a4e&is=669b28ce&hm=6c3429648fb61af51ae6b3f5416d3be44b98fb351b81e8fbbba62f69bea82778&")
        embed.set_author(name="Automated Middleman")

        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            await interaction.response.send_message("Invalid channel ID. Please try again.", ephemeral=True)
            return

        # Create the Select Menu (Dropdown)
        select = CryptoSelect(self.bot)

        # Create a view and add the select menu to it, with no timeout
        view = discord.ui.View(timeout=None)
        view.add_item(select)

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("Embed sent successfully.", ephemeral=True)

class CryptoSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Bitcoin", emoji="<:bitcoin:1256584313487622255>"),
            discord.SelectOption(label="Litecoin", emoji="<:LTC:1256990921036402698>"),
            discord.SelectOption(label="Ethereum", emoji="<:ETHEREUM:936859773700284446>")
        ]
        super().__init__(placeholder="Choose a cryptocurrency...", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category_name = "tickets"
        category = discord.utils.get(guild.categories, name=category_name)

        # Create the category at the top if it doesn't exist
        if category is None:
            category = await guild.create_category(category_name)
            await category.edit(position=0)

        # Determine the starting ticket number based on the cryptocurrency
        selected_crypto = self.values[0].lower()
        if selected_crypto == "bitcoin":
            start_number = 800
            cog_name = 'MiddlemanServiceBTC'
        elif selected_crypto == "litecoin":
            start_number = 4180
            cog_name = 'MiddlemanServiceLTC'
        elif selected_crypto == "ethereum":
            start_number = 204
            cog_name = 'MiddlemanServiceETH'

        # Find the highest ticket number for the selected cryptocurrency
        ticket_number = start_number + sum(1 for channel in category.channels if channel.name.startswith(selected_crypto))

        # Create the channel with specific permissions
        channel_name = f"{selected_crypto}-{ticket_number:04}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)  # Allow the bot to view the channel
        }

        new_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        # Store the selected cryptocurrency in the channel's topic or metadata
        await new_channel.edit(topic=f"crypto={selected_crypto}")

        # Send a response with the link to the new channel
        await interaction.response.send_message(f"✔ Ticket created: {new_channel.mention}", ephemeral=True)

        # Call the appropriate manage_ticket method to manage the ticket
        user_add_cog = self.bot.get_cog('UserAddCog')
        if user_add_cog:
            await user_add_cog.manage_ticket(new_channel, interaction.user, cog_name)

async def setup(bot):
    await bot.add_cog(SetupCog(bot))
