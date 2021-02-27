from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import asyncio
import os
import re

load_dotenv()
SNOOZE_ID = int(os.getenv('SNOOZE_ROLE_ID'))
UOS_ID = int(os.getenv('UOS_ROLE_ID'))


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muted_users = {} # {member_id: [has_uos_role:bool, allow_self_mute:bool]}
        self.allow_self_mute_args_pos = ["true", "t", "yes", "y"]
        self.allow_self_mute_args_neg = ["false", "no", "n", "f"]
        self.re_time = r"([0-9]+)"
        self.re_unit = r"([s|m|h|d|w]{1})"

    @commands.command(aliases=['selfmute'],
                      brief="| Mute yourself.",
                      help=f"Mutes the user.\n\
                      Syntax: >>mute [time] [unit] [allow self unmute]\n\
                      Allowed Units: [s, m, d, w] \n\
                      Allow Self Unmute: [true, t, yes, y, false, f, no, n] \n\
                      Examples: >>mute \n\
                                >>mute 4d\n\
                                >>mute 6 w false"
                      )
    async def mute(self, ctx, arg1=None, arg2=None, arg3=True):
        member = ctx.author
        mute_role = get(member.guild.roles, id=SNOOZE_ID)
        uos_role = get(member.guild.roles, id=UOS_ID)
        time = arg1
        unit = arg2
        allow_self_mute = arg3

        # >>mute 5d True
        if arg2 != None:
            if arg2.lower() in self.allow_self_mute_args_pos:
                allow_self_mute = True
                arg2 = None
            elif arg2.lower() in self.allow_self_mute_args_neg:
                allow_self_mute = False
                arg2 = None

        # Member is already muted -> stop function
        if mute_role in member.roles:
            await ctx.send(f"{member} is already muted. Please wait for your " +
            "mute to finish or >>unmute")
            return

        # Member has UoS role which has to be reassigned after the unmute
        if uos_role in member.roles:
            self.muted_users[member.id] = [True, allow_self_mute]
            await member.remove_roles(uos_role)
        else:
            self.muted_users[member.id] = [False, allow_self_mute]
        await member.add_roles(mute_role)

        # >>mute 5d | split 5d into [5, d]
        if arg1 != None and arg2 == None:
            match = re.match(self.re_time+self.re_unit, arg1, re.I)
            if match:
                time, unit = match.groups()
            else:
                await ctx.send(f"Argument {arg1} not recognized.")
                return
        # >>mute 5 d
        elif arg1 != None and arg2 != None:
            match_time = re.match(self.re_time, arg1, re.I)
            match_unit = re.match(self.re_unit, arg2, re.I)
            if match_time and match_unit:
                time = arg1
                unit = arg2
            else:
                await ctx.send(f"Argument {arg1} or {arg2} not recognized.")
                return

        # Sleeps until it's time to unmute
        if unit == None:
            await ctx.send(f"Muted {member}")
            return
        elif unit == "s":
            wait_time = int(time)
        elif unit == "m":
            wait_time = int(time) * 60
        elif unit == "h":
            wait_time = int(time) * 60 * 60
        elif unit == "d":
            wait_time = int(time) * 60 * 60 * 24
        elif unit == "w":
            wait_time = int(time) * 60 * 60 * 24 * 7

        await ctx.send(f"Muted {member} for {time}{unit} (Self unmute :{str(allow_self_mute).lower()})")
        await asyncio.sleep(wait_time)
        # User could self unmute while timer runs
        if member.id in self.muted_users:
            await self.unmute(ctx, unmute_override=True)


    @commands.command(aliases=[],
                      brief="| Unmute yourself.",
                      help="Unmutes the user.")
    async def unmute(self, ctx, unmute_override=False):
        member = ctx.author
        mute_role = get(member.guild.roles, id=SNOOZE_ID)
        uos_role = get(member.guild.roles, id=UOS_ID)

        # Member is in mute list and can be unmuted
        if member.id in self.muted_users:
            # Member is allowed to unmute themselves. Can be overriten by the
            # mute function when the timer has run out
            if self.muted_users[member.id][1] or unmute_override:
                # Member had the UoS role which has to be reassigned
                if self.muted_users[member.id][0]:
                    await member.add_roles(uos_role)
                await member.remove_roles(mute_role)
                self.muted_users.pop(member.id)
                await ctx.send(f"Unmuted {member}")
            else:
                await ctx.send(f"Can't unmute {member}." \
                "You can only unmute yourself if you have muted yourself.")
        else:
            await ctx.send(f"{member} is not muted or was muted manually by a mod.")

def setup(bot):
    bot.add_cog(Moderation(bot))
