from discord.ext import commands
from dotenv import load_dotenv
import os
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OWNER = os.getenv('DISCORD_ADMIN_ID')
PREFIX = os.getenv('BOT_PREFIX')
description = "A simple bot created to do countdowns for listening parties."
bot = commands.Bot(command_prefix=PREFIX, description=description)


def check_if_it_is_me(ctx):
    return str(ctx.message.author.id) == OWNER


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------------------------')


@bot.command(brief="| Admin command for loading new cog extensions.",
             help="Admin command for loading new cog extensions.",
             hidden=True)
async def load(ctx, extension):
    if check_if_it_is_me(ctx):
        bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'Loading of {extension} successful')
    else:
        await ctx.send("Sorry but you don't have the authorization to execute this command")


@bot.command(brief="| Admin command for unloading cog extensions.",
             help="Admin command for unloading cog extensions.",
             hidden=True)
async def unload(ctx, extension):
    if check_if_it_is_me(ctx):
        bot.unload_extension(f'cogs.{extension}')
        await ctx.send(f'Unloading of {extension} successful')
    else:
        await ctx.send("Sorry but you don't have the authorization to execute this command")


@bot.command(brief="| Admin command for reloading cog extensions.",
             help="Admin command for reloading cog extensions.",
             hidden=True)
async def reload(ctx, extension):
    if check_if_it_is_me(ctx):
        bot.unload_extension(f'cogs.{extension}')
        bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'Reload of {extension} successful')
    else:
        await ctx.send("Sorry but you don't have the authorization to execute this command")


@bot.command(brief="| Link to the bots source code.",
             help="Link to the bots source code.",
             hidden=False)
async def source(ctx):
    await ctx.send('GitHub link to the bots source code: '
                    '<https://github.com/sprunq/PartyTimeBot>')


@bot.command(alias=['change_prefix'],
             brief="| Admin command for changing the bot prefix.",
             help="Admin command for changing the bot prefix.",
             hidden=False)
async def prefix(ctx, arg: str):
    if check_if_it_is_me(ctx):
        global PREFIX
        bot.command_prefix = arg
        os.putenv('BOT_PREFIX', arg)
        PREFIX = os.getenv('BOT_PREFIX')
        await ctx.send(f'Prefix changed to {arg}')
    else:
        await ctx.send("Sorry but you don't have the authorization to execute this command")

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')


bot.run(TOKEN)
