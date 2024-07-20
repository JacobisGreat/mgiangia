import discord
from discord.ext import commands
import os
import asyncio
import json

token = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True  # Enable member intent

bot = commands.Bot(command_prefix='!', intents=intents)

# Replace with the ID of the channel you want to forward embeds to
DESTINATION_CHANNEL_ID = 1264064226385985587

# List of allowed user IDs
ALLOWED_USER_IDS = [1249852943943864340, 234567890123456789]  # Replace with actual user IDs

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
    for filename in os.listdir("./services"):
        if filename.endswith(".py"):
            await bot.load_extension(f"services.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.tree.sync()

@bot.event
async def on_message(message):
    # Check if the message is a DM, is from an allowed user, and contains a JSON payload
    if isinstance(message.channel, discord.DMChannel) and message.author.id in ALLOWED_USER_IDS:
        try:
            embed_dict = json.loads(message.content)
            embed = discord.Embed.from_dict(embed_dict)
            destination_channel = bot.get_channel(DESTINATION_CHANNEL_ID)
            await destination_channel.send(embed=embed)
        except json.JSONDecodeError:
            print("Failed to decode JSON")
    
    # Make sure to process commands if you have any
    await bot.process_commands(message)

async def main():
    async with bot:
        await load_extensions()
        await bot.start(token)

asyncio.run(main())
