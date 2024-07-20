import discord
from discord.ext import commands
import asyncio
import random
import string

class CloseTicketButton(discord.ui.Button):
    def __init__(self, channel):
        super().__init__(label="Close Ticket", style=discord.ButtonStyle.danger)
        self.channel = channel

    async def callback(self, interaction: discord.Interaction):
        await self.channel.delete()
        await interaction.response.send_message("The ticket has been closed and deleted.", ephemeral=True)

class UserAddCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def manage_ticket(self, channel, user, cog_name):
        print(f"[DEBUG] Managing ticket in channel: {channel.name}, for user: {user.name}")
        await self.send_initial_message(channel, user)
        await self.call_middleman_service(channel, cog_name)

    async def send_initial_message(self, channel, user):
        print(f"[DEBUG] Sending initial message in channel: {channel.name}")
        
        # Generate and send transaction ID
        transaction_id = self.generate_transaction_id()
        await channel.send(content=f"```transaction id: {transaction_id}```")

        embed = discord.Embed(
            color=3667300,
            description="eg. @JohnDoe\neg. 123456789123456789",
            title="Who are you dealing with?"
        )
        
        view = discord.ui.View(timeout=None)
        view.add_item(CloseTicketButton(channel))
        
        initial_message = await channel.send(embed=embed, view=view)

        def check(m):
            return m.author == user and m.channel == channel

        while True:
            try:
                print("[DEBUG] Waiting for user response...")
                response = await self.bot.wait_for('message', check=check, timeout=300)
                print(f"[DEBUG] Received user response: {response.content}")
                is_valid, result = await self.validate_user_response(response, channel.guild)
                if is_valid:
                    await self.add_user_to_channel(result, channel)
                    async for message in channel.history(limit=10):
                        if "You can't add yourself to the ticket!" in message.content or "Invalid user!" in message.content:
                            await message.delete()
                    await channel.send(f"{result.mention}")
                    await channel.send(embed=discord.Embed(description=f"Successfully added {result.mention} to the ticket.", color=3667300))
                    print(f"[DEBUG] Successfully added {result.mention} to the ticket.")
                    await initial_message.delete()  # Delete the initial embed after successful addition
                    break
                else:
                    await channel.send(embed=discord.Embed(description=result, color=15608876))
            except asyncio.TimeoutError:
                print("[DEBUG] User response timeout")
                await channel.send(embed=discord.Embed(description="You have run out of time!", color=15608876))
                break

    def generate_transaction_id(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '-' + \
               ''.join(random.choices(string.ascii_lowercase + string.digits, k=4)) + '-' + \
               ''.join(random.choices(string.ascii_lowercase + string.digits, k=4)) + '-' + \
               ''.join(random.choices(string.ascii_lowercase + string.digits, k=4)) + '-' + \
               ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))

    async def validate_user_response(self, message, guild):
        mentioned_users = message.mentions
        user_id = message.content.strip()

        if mentioned_users:
            user = mentioned_users[0]
        else:
            try:
                user = await self.bot.fetch_user(int(user_id))
                member = guild.get_member(user.id)
                if member is None:
                    return False, "This user is not in the server!"
            except (ValueError, discord.NotFound):
                return False, "Invalid user! Please try again."

        member = guild.get_member(user.id)
        if member.bot:
            return False, "You can't add a bot to the ticket!"
        
        if member == message.author:
            return False, "You can't add yourself to the ticket!"

        return True, member

    async def add_user_to_channel(self, user, channel):
        overwrite = discord.PermissionOverwrite()
        overwrite.read_messages = True
        await channel.set_permissions(user, overwrite=overwrite)
        print(f"[DEBUG] Permissions set for {user.name} in channel: {channel.name}")

    async def call_middleman_service(self, channel, cog_name):
        print(f"[DEBUG] Calling middleman service: {cog_name}")
        middleman_cog = self.bot.get_cog(cog_name)
        if middleman_cog:
            await middleman_cog.next_step(channel)
        else:
            print(f"[DEBUG] Middleman service {cog_name} not found")

async def setup(bot):
    await bot.add_cog(UserAddCog(bot))
