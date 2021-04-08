from discord.ext import commands
from dotenv import load_dotenv
import datetime
import logging
import discord
import os

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OWNER = os.getenv('DISCORD_ADMIN_ID')
PREFIX = os.getenv('BOT_PREFIX')
description = "A simple bot created to do countdowns for listening parties."
activity = discord.Game(name=">>help")
bot = commands.Bot(command_prefix=PREFIX, description=description)
ts = datetime.datetime.now()
date = str(ts.strftime("%Y.%m.%d.%H.%M"))
logging.basicConfig(filename=f'{date}.log', filemode='w', format='%(asctime)s %(levelname)-8s [%(filename)s:%(funcName)s] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=activity)
    logging.info('Logged in as %s (%s).', bot.user.name, bot.user.id)


@bot.command(brief="| Admin command for loading new cog extensions.",
             help="Admin command for loading new cog extensions.",
             hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    logging.info('Loaded extension %s.', extension)
    await ctx.send(f'Loading of {extension} successful')


@bot.command(brief="| Admin command for unloading cog extensions.",
             help="Admin command for unloading cog extensions.",
             hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    logging.info('Unloaded extension %s.', extension)
    await ctx.send(f'Unloading of {extension} successful')


@bot.command(brief="| Admin command for reloading cog extensions.",
             help="Admin command for reloading cog extensions.",
             hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    logging.info('Reloaded extension %s.', extension)
    await ctx.send(f'Reload of {extension} successful')


@bot.command(brief="| Link to the bots source code.",
             help="Link to the bots source code.",
             hidden=False)
async def source(ctx):
    await ctx.send('GitHub link to the bots source code: '
                    'https://github.com/sprunq/PartyTimeBot')
    logging.info('Sent source link.')


@bot.command(alias=['change_prefix'],
             brief="| Admin command for changing the bot prefix.",
             help="Admin command for changing the bot prefix.",
             hidden=False)
@commands.is_owner()
async def prefix(ctx, arg: str):
    global PREFIX
    bot.command_prefix = arg
    os.putenv('BOT_PREFIX', arg)
    PREFIX = os.getenv('BOT_PREFIX')
    await ctx.send(f'Prefix changed to {arg}')
    logging.info('Changed prefix to %s.', arg)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        logging.info('Loaded extension %s.', filename[:-3])

bot.run(TOKEN)
