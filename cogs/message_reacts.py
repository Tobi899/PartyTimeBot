import re
from discord.ext import commands
from discord.utils import get
import random


class MessageReact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bonk_trigger_chance = 3
        self.bonk_tag_list = ["sex", "horny", "feet", "choking", "bdsm", "ass", "bonk"]

    @commands.Cog.listener()
    async def on_message(self, message):
        def string_found(string1, string2):
            if re.search(r"\b" + re.escape(string1) + r"\b", string2):
                return True
            return False

        if message.author != self.bot.user:
            msg = message.content.lower()
            if any(string_found(tag, msg) for tag in self.bonk_tag_list):
                if random.randint(0, self.bonk_trigger_chance) == 0:
                    emote = get(self.bot.emojis, name="bonk")
                    if emote:
                        await message.add_reaction(emote)
            
    @commands.command(hidden=True)
    @commands.is_owner()
    async def horny_trigger(self, ctx, chance:int):
        self.bonk_trigger_chance = chance
        await ctx.send(f"set trigger chance to 1/{chance}")

def setup(bot):
    bot.add_cog(MessageReact(bot))
