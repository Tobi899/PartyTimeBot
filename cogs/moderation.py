from discord.ext import commands
from discord.utils import get


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['selfmute'],
                      brief="| Mute yourself.",
                      help="Mutes the user.")
    async def mute(self, ctx):
        member = ctx.author
        role = get(member.guild.roles, name="Snooze")
        await member.add_roles(role)

    @commands.command(aliases=[],
                      brief="| Unmute yourself.",
                      help="Unmutes the user.")
    async def unmute(self, ctx):
        member = ctx.author
        role = get(member.guild.roles, name="Snooze")
        await member.remove_roles(role)


def setup(bot):
    bot.add_cog(Moderation(bot))
