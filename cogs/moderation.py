from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import datetime
import asyncio
import logging
import time
import os
import re
import sqlite3
try:
    import httplib
except:
    import http.client as httplib


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MUTE_ROLE_ID = int(os.getenv('SNOOZE_ROLE_ID'))
        self.UOS_ROLE_ID = int(os.getenv('UOS_ROLE_ID'))
        self.GUILD_ID = int(os.getenv('GUILD_ID'))
        self.OWNER = int(os.getenv('DISCORD_ADMIN_ID'))
        self.MSG_CHANNEL_ID = int(os.getenv('BOT_MSG_CHANNEL_ID'))
        self.database = sqlite3.connect('moderation.db')
        self.cursor = self.database.cursor()

        # Create mute table if it doesn't exist
        self.cursor.execute(
            ''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='mute' ''')
        if self.cursor.fetchone()[0] == 1:
            logging.info('Created Database table already exists')
        else:
            self.cursor.execute("""CREATE TABLE mute (
                        mute_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        member_id INTEGER,
                        unmute_date_unix INTEGER,
                        has_uos_role BOOL
                        )""")
            logging.info('Created Database table')
        self.database.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("Auto unmute started.")
        try:
            self.cursor.execute("SELECT * FROM mute")
            res = self.cursor.fetchall()
            if len(res) <= 0:
                return

            def getUnixKey(elem):
                return elem[2]
            res.sort(key=getUnixKey)
            for entry in res:
                logging.info("Auto unmute started for: [%s, %s, %s, %s] ", entry[0], entry[1], entry[2], entry[3])
                time_end = entry[2]
                time_now = int(time.time())
                rel_time = time_end - time_now
                if rel_time > 0:
                    await asyncio.sleep(rel_time)
                await self.internalUnmute(entry[1], entry[0])
            logging.info("Auto unmute finished.")
        except Exception as Argument:
            logging.exception("Error occured in autoUnmute")

    @commands.command(aliases=["addentry", "add"],
                      brief="| Add user to DB.",
                      help=f"Add user to DB.",
                      hidden=True)
    @commands.is_owner()
    async def addToDb(self, ctx, member_id, unmute_date_unix, has_uos_role):
        logging.info('%s trying to add to DB: [%s, %s]', member_id, unmute_date_unix, has_uos_role)
        try:
            member_id = int(member_id)
            unmute_date_unix = int(unmute_date_unix)
            has_uos_role = int(has_uos_role)
            self.addUserToDB(member_id, unmute_date_unix, has_uos_role)
            await ctx.send(f"Added {member_id} to db ({unmute_date_unix}, {has_uos_role})")
        except ValueError:
            await ctx.send("Arguments don't match the types")
            logging.error("%s can't add to DB. Types do not match: [%s, %s]", member_id, unmute_date_unix, has_uos_role)

    @commands.command(aliases=["removeentry", "rem"],
                      brief="| Remove user from DB.",
                      help=f"Remove User from DB.",
                      hidden=True)
    @commands.is_owner()
    async def removeFromDb(self, ctx, member_id):
        logging.info('Trying to delete from DB: [%s]', member_id)
        try:
            member_id = int(member_id)
            self.removeUserFromDB(member_id)
            await ctx.send(f"Removed {member_id} from db")
        except ValueError:
            await ctx.send("Argument doesn't match the type")
            logging.error("Can't delete from DB. Type does not match: [%s]", member_id)

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
    async def mute(self, ctx, timeframe=None, unit=None):
        try:
            member = ctx.author
            mute_role = get(member.guild.roles, id=self.MUTE_ROLE_ID)
            uos_role = get(member.guild.roles, id=self.UOS_ROLE_ID)

            logging.info('%s starting mute', member.id)

            if mute_role in member.roles:
                await ctx.send("You are already muted. Please wait for your unmute to finish or >>unmute")
                logging.error('%s is already muted', member.id)
                return

            # Args processing
            if timeframe is not None and unit is not None:
                valid_time = re.match(r"([0-9]*[.])?[0-9]+", timeframe)
                valid_unit = re.match(r"([m|h|d|w]{1})", unit)
                if valid_time and valid_unit:
                    time_arg = timeframe
                    mute_unit = unit
                else:
                    await ctx.send("Arguments not recognized")
                    logging.error('%s arguments not recognized [%s, %s]', member.id, timeframe, unit)
                    return
            elif timeframe is not None and unit is None:
                await ctx.send("Arguments not recognized")
                logging.error('%s arguments not recognized [%s, %s]', member.id, timeframe, unit)
                return
            else:
                # No args given
                time_arg = 0
                mute_unit = "unlimited"

            sleep_duration = self.getSleepDuration(time_arg, mute_unit)
            unix_time_end = self.relativeTimeToUnixTimestamp(sleep_duration)
            # Check if user has uos_role role (need to reassign on unmute)
            if uos_role in member.roles:
                has_uos_role = True
            else:
                has_uos_role = False

            # Replace previous existing entry with the member_id from the db with new one
            self.removeUserFromDB(member.id)
            self.addUserToDB(member.id, unix_time_end, has_uos_role)

            self.cursor.execute("SELECT last_insert_rowid()")
            mute_id = self.cursor.fetchone()[0]

            if has_uos_role:
                await member.remove_roles(uos_role)
            await member.add_roles(mute_role)

            if timeframe == None or unit == None:
                await ctx.send(f"Muted {member}")
                logging.info("%s muted", member.id)
            else:
                await ctx.send(f"Muted {member} for {timeframe}{unit}")
                logging.info("%s muted for %s%s", member.id, timeframe, unit)

            if mute_unit != "unlimited":
                await asyncio.sleep(sleep_duration)
                await self.internalUnmute(member.id, mute_id)
        except Exception as Argument:
            logging.exception("Error occured while trying to mute %s", member.id)

    @commands.command(aliases=["selfunmute"],
                      brief="| Unmute yourself.",
                      help="Unmutes the user.")
    async def unmute(self, ctx):
        try:
            member = ctx.author
            logging.info("%s starting unmuted", member.id)

            mute_role = get(member.guild.roles, id=self.MUTE_ROLE_ID)
            uos_role = get(member.guild.roles, id=self.UOS_ROLE_ID)

            self.cursor.execute("SELECT * FROM mute WHERE member_id=?", (member.id,))
            res = self.cursor.fetchall()
            if len(res) <= 0:
                await ctx.send("I can't find you in my database. Please message the staff or sprung")
                logging.error("%s can't be found in DB", member.id)
                return

            has_uos_role = res[0][3]
            await member.remove_roles(mute_role)
            if has_uos_role:
                await member.add_roles(uos_role)

            self.removeUserFromDB(member.id)
            if ctx != None:
                await ctx.send(f"Unmuted {member}")
                logging.info("%s unmuted", member.id)
        except Exception as Argument:
            logging.exception("Error occured while trying to unmute %s", mute.id)

    @commands.command(aliases=["pdb"],
                      brief="-",
                      help="Prints the DB",
                      hidden=True)
    async def printDB(self, ctx):
        try:
            logging.info("Printing DB.")
            self.cursor.execute("Select * from mute")
            res = self.cursor.fetchall()
            string = ""
            chunks = []
            for entry in res:
                rel_time = entry[2] - int(time.time())
                e_uos = "True" if entry[3] else "False"
                string += f"[Mute ID: {entry[0]}, Member ID: {entry[1]}, Unmute Unix: {entry[2]} ({self.relativeTimeToHours(rel_time)} hrs), " \
                    + f"Has Uos Role: {e_uos}]\n"
                if len(string) > 1900:
                    chunks.append(string)
                    string = ""
            chunks.append(string)
            for str in chunks:
                await ctx.send("```Muted Users:\n" + str + "```")
            logging.info("Printing DB done.")
        except Exception as Argument:
            logging.exception("Error occured while printing Database")

    async def internalUnmute(self, member_id, call_mute_id):
        logging.info("InternalUnmute started: %s", member_id)
        while not self.internetConnAvailable():
            await asyncio.sleep(300)
            logging.error("No internet connection available for %s", member_id)
        try:
            guild = await self.bot.fetch_guild(self.GUILD_ID)
            member = await guild.fetch_member(member_id)
        except NameError:
            logging.error("Couldn't fetch member or roles %s", member_id)
            return
        mute_role = get(member.guild.roles, id=self.MUTE_ROLE_ID)
        uos_role = get(member.guild.roles, id=self.UOS_ROLE_ID)

        self.cursor.execute("SELECT * FROM mute WHERE member_id=?", (member.id,))
        res = self.cursor.fetchone()
        if len(res) <= 0:
            return

        mute_id_now = res[0]
        if call_mute_id != mute_id_now:
            logging.error("Mute_Ids not matching [%s, %s]", call_mute_id, mute_id_now)
            return

        has_uos_role = res[3]
        await member.remove_roles(mute_role)
        if has_uos_role:
            await member.add_roles(uos_role)
        self.removeUserFromDB(member.id)
        logging.info("Internal unmute successful: %s", member_id)

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

    def relativeTimeToUnixTimestamp(self, mute_duration):
        timesptamp = int(time.time()) + mute_duration
        if timesptamp > 9223372036854775807 or mute_duration == -1:
            timesptamp = 9223372036854775807
        return timesptamp

    def relativeTimeToHours(self, rel_time):
        return round(((rel_time) / 60 / 60), 2)

    def removeUserFromDB(self, member_id):
        self.cursor.execute("""DELETE FROM mute
                            WHERE member_id = :member_id""",
                       {'member_id': member_id, })
        self.database.commit()
        logging.info('%s removed from DB', member_id)

    def addUserToDB(self, member_id, unix_time_end, has_uos_role):
        self.cursor.execute("""INSERT INTO mute
                            VALUES (:mute_id, :member_id, :unmute_date_unix,
                            :has_uos_role)""",
                           {'mute_id': None,
                            'member_id': member_id,
                            'unmute_date_unix': unix_time_end,
                            'has_uos_role': has_uos_role,
                            })
        self.database.commit()
        logging.info('%s added to DB: [%s, %s]', member_id, unix_time_end, has_uos_role)

    def internetConnAvailable(self):
        conn = httplib.HTTPConnection("www.google.com", timeout=5)
        try:
            conn.request("HEAD", "/")
            conn.close()
            return True
        except:
            conn.close()
            return False


def setup(bot):
    bot.add_cog(Moderation(bot))
