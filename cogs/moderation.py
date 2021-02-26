from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import os
load_dotenv()
SNOOZE_ID = int(os.getenv('SNOOZE_ROLE_ID'))
UOS_ID = int(os.getenv('UOS_ROLE_ID'))

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.has_UoS_role = []

    @commands.command(aliases=['selfmute'],
                      brief="| Mute yourself.",
                      help="Mutes the user.")
    async def mute(self, ctx):
        member = ctx.author
        mute_role = get(member.guild.roles, id=SNOOZE_ID)
        uos_role = get(member.guild.roles, id=UOS_ID)
        member_roles = member.roles

        for role in member_roles:
            if role == uos_role:
                self.has_UoS_role.append(member.id)
                await member.remove_roles(uos_role)
        await member.add_roles(mute_role)
        await ctx.send(f"Muted {member}")


    @commands.command(aliases=[],
                      brief="| Unmute yourself.",
                      help="Unmutes the user.")
    async def unmute(self, ctx):
        member = ctx.author
        mute_role = get(member.guild.roles, id=SNOOZE_ID)
        uos_role = get(member.guild.roles, id=UOS_ID)

        if member.id in self.has_UoS_role:
            self.has_UoS_role.remove(member.id)
            await member.add_roles(uos_role)
        await member.remove_roles(mute_role)
        await ctx.send(f"Unmuted {member}")


def setup(bot):
    bot.add_cog(Moderation(bot))
