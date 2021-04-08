from discord.ext import commands
import random
import logging


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=[],
                      brief="| Check if bot is operational.",
                      help="Check if bot is operational.")
    async def ping(self, ctx):
        await ctx.send("Pong!")
        logging.info('Pong successful.')

    @commands.command(aliases=['roll'],
                      brief="| Rolls a random number between 0 and the given integer.",
                      help="Rolls a random number between 0 and the given integer.")
    async def random(self, ctx, arg):
        try:
            arg = int(arg)
            await ctx.send(f"You rolled a {str(random.randrange(0, arg))}")
            logging.info('Random with max digit count %s.', len(str(arg)))
        except ValueError:
            await ctx.send("Please enter a valid number")
            logging.error('Random with max digit count %s failed. Arg: %s', len(str(arg)), arg)


def setup(bot):
    bot.add_cog(Utility(bot))
