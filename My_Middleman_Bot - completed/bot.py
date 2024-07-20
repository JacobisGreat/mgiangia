import discord
from discord.ext import commands
import os
import asyncio
token = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True  # Enable member intent

bot = commands.Bot(command_prefix='!', intents=intents)

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.tree.sync()

async def main():
    async with bot:
        await load_extensions()
        await bot.start(token)

asyncio.run(main())
