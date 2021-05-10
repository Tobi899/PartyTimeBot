from discord.ext import commands
import random


class GoodMorning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author != self.bot.user:
            if random.randint(0, 100) == 0:
                if "good morning" in message.content.lower():
                    await message.channel.send("Good Morning")


def setup(bot):
    bot.add_cog(GoodMorning(bot))
