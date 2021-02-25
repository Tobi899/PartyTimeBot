from discord.ext import commands
from discord.utils import get


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.has_UoS_role = []

    @commands.command(aliases=['selfmute'],
                      brief="| Mute yourself.",
                      help="Mutes the user.")
    async def mute(self, ctx):
        member = ctx.author
        mute_role = get(member.guild.roles, name="Snooze")
        member_roles = member.roles
        for role in member_roles:
            if role.name == "UoS Coat of Scrobbles":
                self.has_UoS_role.append(member.id)
                uos_role = get(member.guild.roles, name="UoS Coat of Scrobbles")
                await member.remove_roles(uos_role)
        await member.add_roles(mute_role)

    @commands.command(aliases=[],
                      brief="| Unmute yourself.",
                      help="Unmutes the user.")
    async def unmute(self, ctx):
        member = ctx.author
        mute_role = get(member.guild.roles, name="Snooze")
        uos_role = get(member.guild.roles, name="UoS Coat of Scrobbles")
        if member.id in self.has_UoS_role:
            self.has_UoS_role.remove(member.id)
            await member.add_roles(uos_role)
        await member.remove_roles(mute_role)


def setup(bot):
    bot.add_cog(Moderation(bot))
