from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import asyncio
import time
import os
import re
import sqlite3

load_dotenv()


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sleep_threads = []
        self.mute_role_id = int(os.getenv('SNOOZE_ROLE_ID'))
        self.uos_role_id = int(os.getenv('UOS_ROLE_ID'))
        self.guild_id = int(os.getenv('GUILD_ID'))
        self.OWNER = int(os.getenv('DISCORD_ADMIN_ID'))
        self.re_time = r"([0-9]*[.])?[0-9]+"
        self.re_unit = r"([m|h|d|w]{1})"
        self.allow_self_mute_args_pos = ["true", "t", "yes", "y"]
        self.allow_self_mute_args_neg = ["false", "no", "n", "f"]
        self.db = sqlite3.connect('moderation.db')
        self.c = self.db.cursor()

        # Create mute table if it doesn't exist
        self.c.execute(
            ''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='mute' ''')
        if self.c.fetchone()[0] == 1:
            print("Database exists")
        else:
            self.c.execute("""CREATE TABLE mute (
                        mute_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        member_id INTEGER,
                        unmute_date_unix INTEGER,
                        has_uos_role BOOL,
                        allow_self_unmute BOOL
                        )""")
            print("Database created")
        self.db.commit()

    @commands.command(aliases=["selfmute"],
                      brief="| Mute yourself.",
                      help=f"Mutes the user.\n\
                      Syntax: >>mute [time] [unit] [allow self unmute]\n\
                      Unit args: [s, m, d, w] \n\
                      Self Unmute args: [true, t, yes, y, false, f, no, n] \n\
                      Examples: >>mute \n\
                                >>mute 4 d\n\
                                >>mute 6 w false"
                      )
    async def mute(self, ctx, timeframe=None, unit=None, allow_self_unmute="True"):
        member = ctx.author
        # Get roles
        mute_role = get(member.guild.roles, id=self.mute_role_id)
        uos_role = get(member.guild.roles, id=self.uos_role_id)

        if mute_role in member.roles:
            await ctx.send("You are already muted. Please wait for your unmute to finish or >>unmute")
            return

        # Args processing
        if all(v is not None for v in [timeframe, unit, allow_self_unmute]):
            # All args have values
            valid_time = re.match(self.re_time, timeframe)
            valid_unit = re.match(self.re_unit, unit)
            if allow_self_unmute.lower() in self.allow_self_mute_args_pos:
                allow_self_unmute = True
            elif allow_self_unmute.lower() in self.allow_self_mute_args_neg:
                allow_self_unmute = False
            else:
                allow_self_unmute = None

            if valid_time and valid_unit and allow_self_unmute is not None:
                time_arg = timeframe
                mute_unit = unit
            else:
                await ctx.send("Arguments not recognized")
        else:
            # No args given
            time_arg = 0
            mute_unit = "unlimited"
            allow_self_unmute = True

        # Calculate mute duration
        sleep_duration = self.getSleepDuration(time_arg, mute_unit)
        # Get mute duration
        unmute_date_unix = self.getMuteEndUnixTimestamp(sleep_duration)

        # Check if user has uos_role role (need to reassign on unmute)
        if uos_role in member.roles:
            has_uos_role = True
            await member.remove_roles(uos_role)
        else:
            has_uos_role = False

        # Remove all previously existing entries with the member_id from the db
        self.c.execute("""DELETE FROM mute
                            WHERE member_id = :member_id""",
                       {'member_id': member.id, })

        # Add new db entry
        self.c.execute("""INSERT INTO mute
                            VALUES (:mute_id, :member_id, :unmute_date_unix,
                            :has_uos_role, :allow_self_unmute)""",
                       {'mute_id': None,
                        'member_id': member.id,
                        'unmute_date_unix': unmute_date_unix,
                        'has_uos_role': has_uos_role,
                        'allow_self_unmute': allow_self_unmute
                        })
        self.db.commit()
        await member.add_roles(mute_role)
        if timeframe == None or unit == None:
            await ctx.send(f"Muted {member} (Allow self unmute: {allow_self_unmute})")
        else:
            await ctx.send(f"Muted {member} for {timeframe}{unit} (Allow self unmute: {allow_self_unmute})")

        if mute_unit != "unlimited":
            await asyncio.sleep(sleep_duration)
            await self.unmute(ctx=ctx, member_id=member.id, override=True)

    @commands.command(aliases=["selfunmute"],
                      brief="| Unmute yourself.",
                      help="Unmutes the user.")
    async def unmute(self, ctx, member_id=None, override="False"):
        override = override == "True"
        if member_id == None:
            member = ctx.author
        elif member_id != None:
            guild = await self.bot.fetch_guild(self.guild_id)
            member = await guild.fetch_member(member_id)

        # Get roles
        mute_role = get(member.guild.roles, id=self.mute_role_id)
        uos_role = get(member.guild.roles, id=self.uos_role_id)

        self.c.execute("SELECT * FROM mute WHERE member_id=?", (member.id,))
        res = self.c.fetchall()
        if len(res) <= 0:
            # await ctx.send("User not muted")
            return
        mute_id = res[0][0]
        member_id = res[0][1]
        has_uos_role = res[0][3]
        allow_self_unmute = res[0][4]

        if not override:
            if not allow_self_unmute:
                await ctx.send("Self unmute disabled. If you want in regardless message Pingu or sprung")
                return
        else:
            if ctx.message.author.id != self.OWNER:
                await ctx.send("You don't have the permission to unmute other users")
                return

        await member.remove_roles(mute_role)
        if has_uos_role:
            await member.add_roles(uos_role)
        self.c.execute("""DELETE FROM mute
                            WHERE member_id = :member_id""",
                       {'member_id': member.id, })
        self.db.commit()
        if ctx != None:
            await ctx.send(f"Unmuted {member}")

    @commands.command(aliases=["restartUnmute", "sumt"],
                      brief="Restarts auto unmute timers",
                      help="Restarts auto unmute timers.",
                      hidden=True)
    async def autoUnmute(self, ctx):
        """
        Restarts automatic unmutes.
        """
        if ctx.message.author.id != self.OWNER and ctx != None:
            await ctx.send("You don't have the permission to use this command")
            return
        self.c.execute("SELECT * FROM mute")
        res = self.c.fetchall()
        if len(res) <= 0:
            print("No users muted")
            return
        # Sort list by Unix unmute timesptamp
        # Get relative time until time_end for closest timestamp and sleep for that long
        # Unmute after sleep end
        # Repeat for each element

        def getUnixKey(elem):
            return elem[2]
        res.sort(key=getUnixKey)
        for entry in res:
            print(f"starting sleep")
            print(entry)
            time_end = entry[2]
            time_now = int(time.time())
            relative_time_in_secs = time_end - time_now
            if relative_time_in_secs > 0:
                await asyncio.sleep(relative_time_in_secs)
            await self.unmute(ctx=ctx, member_id=entry[1], override="True")
            print(f"Unmuted {entry[1]}")

    @commands.command(aliases=["pdb"],
                      brief="-",
                      help="Prints the DB",
                      hidden=True)
    async def printDB(self, ctx):
        self.c.execute("Select * from mute")
        res = self.c.fetchall()
        string = ""
        for entry in res:
            rel_time = round(((entry[2] - int(time.time())) / 60 / 60), 2)
            e_uos = "True" if entry[3] else "False"
            e_asu = "True" if entry[4] else "False"
            string += f"[Mute ID: {entry[0]}, Member ID: {entry[1]}, Unmute Unix: {entry[2]} ({rel_time} hrs), " \
                + f"Has Uos Role: {e_uos}, Allow Self Unmute: {e_asu}]\n"
        await ctx.send("```Muted users:\n" + string + "```")

    def getSleepDuration(self, time_arg, mute_unit):
        # Calculate mute duration
        if mute_unit == "m":
            sleep_time = float(time_arg) * 60  # Minutes
        elif mute_unit == "h":
            sleep_time = float(time_arg) * 60 * 60  # Hours
        elif mute_unit == "d":
            sleep_time = float(time_arg) * 60 * 60 * 24  # Days
        elif mute_unit == "w":
            sleep_time = float(time_arg) * 60 * 60 * 24 * 7  # Weeks
        elif mute_unit == "unlimited":
            sleep_time = -1
        return int(sleep_time)

    def getMuteEndUnixTimestamp(self, mute_duration):
        timesptamp = int(time.time()) + mute_duration
        if timesptamp > 9223372036854775807 or mute_duration == -1:
            timesptamp = 9223372036854775807
        return timesptamp


def setup(bot):
    bot.add_cog(Moderation(bot))
