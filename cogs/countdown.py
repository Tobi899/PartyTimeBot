from discord.ext import commands
import asyncio


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
        self.abort = False

    @commands.command(aliases=['cd', 'count', 'partytime'],
                      brief="| A countdown for listening parties. 1hr (3600) max.",
                      help="A countdown for listening parties. 1hr (3600) max.")
    async def countdown(self, ctx, arg):
        self.abort = True
        try:
            arg = int(arg)
            if arg >= 3600:
                await ctx.send("Please enter a valid integer")
            else:
                while self.abort and arg >= 0:
                    if arg >= 30:
                        msg = switch_countdown(arg)
                        if msg != "don't send":
                            await ctx.send(msg)
                    elif (15 > arg > 5) and (arg % 2 == 0):
                        await ctx.send(arg)
                    elif arg <= 5:
                        await ctx.send(arg)
                    arg = arg - 1
                    await asyncio.sleep(1)

        except ValueError:
            await ctx.send("Please enter an integer <=3600")

    @commands.command(aliases=['cdb', 'countbar' 'partytimebar'],
                      brief="| A countdown for listening parties in bar chart style.",
                      help="A countdown for listening parties in bar chart style."
                      " Set to 10 seconds.")
    async def countdownbar(self, ctx):
        msg_array = [":white_large_square:"] * 10
        msg_to_edit = await ctx.send("".join(msg_array))
        for i in range(10):
            msg_array[i] = ":red_square:"
            await msg_to_edit.edit(content="".join(msg_array))
            await asyncio.sleep(1)

    @commands.command(aliases=['exit', 'reset'],
                      brief="| Stops the current countdown.",
                      help="Stops the current countdown.")
    async def abort(self, ctx):
        self.abort = False


def setup(bot):
    bot.add_cog(Partytime(bot))
