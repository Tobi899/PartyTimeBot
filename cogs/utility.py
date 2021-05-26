import logging
import os
import random

import discord
import asyncpraw
from discord.ext import commands
from flickrapi import FlickrAPI


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.flickr = FlickrAPI(os.getenv('FLICKR_KEY'),
                                os.getenv('FLICKR_SECRET'),
                                format="parsed-json"
                                )
        self.reddit = asyncpraw.Reddit(client_id=os.getenv('REDDIT_ID'),
                                       client_secret=os.getenv('REDDIT_SECRET'),
                                       password=os.getenv('REDDIT_PASSWORD'),
                                       user_agent=os.getenv('REDDIT_USER_AGENT'),
                                       username=os.getenv('REDDIT_USERNAME')
                                       )

    @commands.command(aliases=[],
                      brief="| Check if bot is operational.",
                      help="Check if bot is operational.")
    async def ping(self, ctx):
        await ctx.send("Pong!")
        logging.info('Pong successful.')

    @commands.command(aliases=['roll'],
                      brief="| Rolls a random number between 0 and the given integer.",
                      help="Rolls a random number between 0 and the given integer.")
    async def random(self, ctx, arg):
        try:
            arg = int(arg)
            await ctx.send(f"You rolled a {str(random.randrange(0, arg))}")
            logging.info('Random with max digit count %s.', len(str(arg)))
        except ValueError:
            await ctx.send("Please enter a valid number")
            logging.error('Random with max digit count %s failed. Arg: %s', len(str(arg)), arg)

    async def getFlickrImage(self, tag):
        extras = ["url_c", "url_z", "url_m", "url_l", "url_k", "url_o"]
        page = random.randint(1, 30)
        query = self.flickr.photos.search(text=tag,
                                          page=page,
                                          per_page=1,
                                          extras=",".join(extras),
                                          privacy_filter=1,
                                          sort='relevance')
        photos = query["photos"]
        url = None
        permalink = "https://www.flickr.com/photos/" + photos["photo"][0]["owner"] + "/" + photos["photo"][0]["id"]
        for url_attr in extras:
            try:
                url = photos["photo"][0][url_attr]
                break
            except KeyError:
                pass
        return url, permalink

    async def getRedditImage(self, tag):
        limit = 50
        submissions = []
        subreddit = await self.reddit.subreddit(tag)
        async for s in subreddit.top(time_filter="all", limit=limit):
            d = {
                "is_self": s.is_self,
                "url": s.url,
                "permalink": s.permalink
            }
            submissions.append(d)
        url = None
        permalink = None
        reps = 0
        while url is None:
            rnd = random.randint(0, limit - 1)
            if submissions[rnd]["url"][-3:] in ["jpg", "png"]:
                url = submissions[rnd]["url"]
                permalink = "https://www.reddit.com" + submissions[rnd]["permalink"]
            reps += 1
            if reps > 200:
                break

        return url, permalink

    @commands.command(aliases=["animal"],
                      brief="| Get cute (and not so cute) animal pictures.",
                      help="Supported search terms:\n"
                           "Bird, Quokka, Possum, Cat, Axolotl, Blahaj, Red Panda")
    async def img(self, ctx, *, arg):
        logging.info('Running image for %s', arg)
        accepted_terms = {"bird": ["birds", "birdpics"],
                          "quokka": ["quokka"],
                          "possum": ["possums", "opossums"],
                          "cat": ["cats", "catsareliquid", "illegallysmolcats", "tightpussy", "blurrycats"],
                          "axolotl": ["axolotls"],
                          "blahaj": ["blahaj"],
                          "haj": ["blahaj"],
                          "red panda": ["redpandas"]
                          }
        try:
            arg = arg.lower()
            if arg in accepted_terms:
                if random.randint(0, 3) == 0:
                    if arg == "haj":
                        arg = "blahaj"
                    url, permalink = await self.getFlickrImage(arg)
                else:
                    sub = random.choice(accepted_terms[arg])
                    url, permalink = await self.getRedditImage(sub)
                if url is not None:
                    embed = discord.Embed(title=arg)
                    embed.description = f"[Link]({permalink})"
                    embed.set_image(url=url)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Error :(")
            else:
                logging.error('Invalid search tag %s', arg)
                await ctx.send("Invalid search term")
        except Exception as Argument:
            logging.exception("Error occurred in img")


def setup(bot):
    bot.add_cog(Utility(bot))
