from discord.ext import commands
import asyncio
import logging


def switch_countdown(argument):
    switcher = {
        3600: "60 Minutes left until countdown ends",
        1800: "30 Minutes left until countdown ends",
        600: "10 Minutes left until countdown ends",
        300: "5 Minutes left until countdown ends",
        120: "2 Minutes left until countdown ends",
        60: "1 Minute left until countdown ends",
        30: "30 Seconds left until countdown ends"
    }
    return switcher.get(argument, "don't send")


class Partytime(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['cd', 'count', 'partytime'],
                      brief="| A countdown for listening parties. 1hr (3600) max.",
                      help="A countdown for listening parties. 1hr (3600) max.")
    async def countdown(self, ctx, arg):
        logging.info('Countdown with %s started.', arg)
        cd = arg
        try:
            cd = int(cd)
            if cd > 3600:
                await ctx.send("Please enter a number <=3600")
            else:
                while cd >= 0:
                    if cd >= 30:
                        msg = switch_countdown(cd)
                        if msg != "don't send":
                            await ctx.send(msg)
                    elif (15 > cd > 5) and (cd % 2 == 0):
                        await ctx.send(cd)
                    elif cd <= 5:
                        await ctx.send(cd)
                    cd = cd - 1
                    await asyncio.sleep(1)
            logging.info("Countdown with %s ended.", arg)
        except ValueError:
            await ctx.send("Please enter a number <=3600")
            logging.error('Invalid number %s.', arg)

    @commands.command(aliases=['cdb', 'cbd','countbar' 'partytimebar', 'elsegetyourshittogether'],
                      brief="| A countdown for listening parties in bar chart style.",
                      help="A countdown for listening parties in bar chart style."
                      " Set to 10 seconds.")
    async def countdownbar(self, ctx):
        logging.info('Bar countdown started.')
        msg_array = [":white_large_square:"] * 10
        msg_to_edit = await ctx.send("".join(msg_array))
        for i in range(10):
            msg_array[i] = ":red_square:"
            await msg_to_edit.edit(content="".join(msg_array))
            await asyncio.sleep(1)
        logging.info('Bar countdown ended.')

def setup(bot):
    bot.add_cog(Partytime(bot))
