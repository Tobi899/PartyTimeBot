from discord.ext import commands
from discord.utils import get
import pickle
import os
from dotenv import load_dotenv
load_dotenv()
SNOOZE_ID = int(os.getenv('SNOOZE_ROLE_ID'))
UOS_ID = int(os.getenv('UOS_ROLE_ID'))


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        uos_member_list = []

    @commands.command(aliases=['selfmute'],
                      brief="| Mute yourself.",
                      help="Mutes the user.")
    async def mute(self, ctx):
        member = ctx.author
        mute_role = get(member.guild.roles, id=SNOOZE_ID) # Snooze
        member_roles = member.roles

        for role in member_roles:
            if role.id == UOS_ID: # UoS
                uos_role = get(member.guild.roles, id=UOS_ID) # UoS
                try:
                    with open('uos_users.data', 'rb') as filehandle:
                        try:
                            uos_member_list = pickle.load(filehandle)
                        except EOFError:
                            # Empty file
                            uos_member_list = []
                        # Remove duplicates
                        uos_member_list.append(member.id)
                        uos_member_list = list(dict.fromkeys(uos_member_list))
                except FileNotFoundError:
                    # File doesn't exist
                    uos_member_list = []
                with open('uos_users.data', 'wb') as filehandle:
                    pickle.dump(uos_member_list, filehandle)
                await member.remove_roles(uos_role)
        await member.add_roles(mute_role)

    @commands.command(aliases=[],
                      brief="| Unmute yourself.",
                      help="Unmutes the user.")
    async def unmute(self, ctx):
        member = ctx.author
        mute_role = get(member.guild.roles, id=SNOOZE_ID) # Snooze
        uos_role = get(member.guild.roles, id=UOS_ID)
        try:
            with open('uos_users.data', 'rb') as filehandle:
                try:
                    uos_member_list = pickle.load(filehandle)
                except EOFError:
                    uos_member_list = []
                if member.id in uos_member_list:
                    uos_member_list.remove(member.id)
                    await member.add_roles(uos_role)
        except FileNotFoundError:
            # File doesn't exist
            uos_member_list = []

        with open('uos_users.data', 'wb') as filehandle:
            pickle.dump(uos_member_list, filehandle)
        await member.remove_roles(mute_role)


def setup(bot):
    bot.add_cog(Moderation(bot))
