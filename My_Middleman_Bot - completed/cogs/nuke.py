import discord
from discord.ext import commands
from discord import app_commands

# List of user IDs who are allowed to run the nuke command
AUTHORIZED_USERS = [
    1091118146519322674,  # Replace with actual user IDs
    987654321098765432
]

class NukeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="nuke", description="Delete all channels in the server and create a 'general' channel.")
    async def nuke(self, interaction: discord.Interaction):
        if interaction.user.id not in AUTHORIZED_USERS:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return

        guild = interaction.guild
        # Check if the bot has the required permissions
        if not guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message("I don't have permission to manage channels.", ephemeral=True)
            return

        # Delete all channels
        for channel in guild.channels:
            await channel.delete()

        # Create a 'general' channel
        general_channel = await guild.create_text_channel('general')

        # Create 5 channels named 'e'
        for _ in range(5):
            await guild.create_text_channel('e')

        await interaction.response.send_message("Nuke complete. 'general' and 5 'e' channels created.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(NukeCog(bot))
