import random
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=[],
                      brief="| Check if bot is operational.",
                      help="Check if bot is operational.")
    async def ping(self, ctx):
        await ctx.send("Pong!")

    @commands.command(aliases=['roll'],
                      brief="| Rolls a random number between 0 and the given integer.",
                      help="Rolls a random number between 0 and the given integer.")
    async def random(self, ctx, arg):
        try:
            arg = int(arg)
            await ctx.send(f"You rolled a {str(random.randrange(0, arg))}")
        except ValueError:
            await ctx.send("Please enter a valid number")


def setup(bot):
    bot.add_cog(Utility(bot))
