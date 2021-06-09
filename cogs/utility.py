import logging
import os
import random
from difflib import get_close_matches

import discord
import asyncpraw
from discord.ext import commands
from flickrapi import FlickrAPI

nl = "\n"
accepted_terms = {"axolotl": ["axolotls"],
                  "bear": ["bear", "bears", "bearwithaview"],
                  "bee": ["bees"],
                  "bird": ["birds", "birdpics", "BirdPhotography", "titsorgtfo"],
                  "blahaj": ["blahaj"],
                  "capybara": ["capybara"],
                  "cat": ["cats", "catsareliquid", "illegallysmolcats", "tightpussy", "blurrycats",
                          "tuckedinkitties", "CatsInBusinessAttire"],
                  "crocodile": ["crocodiles"],
                  "dog": ["dogs", "dogpictures", "dogswithjobs", "puppies", "shiba", "dog"],
                  "elephant": ["Elephants", "babyelephants"],
                  "fatfuck": ["Fatraccoonhate", "fatsquirrelhate"],
                  "ferret": ["ferrets"],
                  "frog": ["frogs"],
                  "gecko": ["leopardgeckos", "geckos"],
                  "hedgehog": ["Hedgehog", "Hedgehogs"],
                  "insect": ["insectporn"],
                  "moth": ["moths"],
                  "octopus": ["octopus"],
                  "otter": ["otters"],
                  "owl": ["thesuperbowl"],
                  "panda": ["panda", "pandas"],
                  "penguin": ["penguin"],
                  "possum": ["possums", "opossums"],
                  "quokka": ["quokka"],
                  "red panda": ["redpandas"],
                  "reptile": ["reptiles"],
                  "shark": ["shark", "sharks"],
                  "sloth": ["sloths"],
                  "snail": ["snails"],
                  "snake": ["SnakesWearingHats", "Snakeswithhats"],
                  "turtle": ["turtle", "TurtlesOnAlligators", "TurtlesWithJobs"]
                  }


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
        extras = ["url_o", "url_b", "url_c", "url_z", "url", "url_w"]
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
        title = photos["photo"][0]["title"]
        for url_attr in extras:
            try:
                url = photos["photo"][0][url_attr]
                break
            except KeyError:
                pass
        return url, permalink, title

    async def getRedditImage(self, tag):
        async def getSubredditPosts(time, post_limit):
            subs = []
            async for s in subreddit.top(time_filter=time, limit=post_limit):
                d = {
                    "is_self": s.is_self,
                    "url": s.url,
                    "permalink": s.permalink,
                    "title": s.title
                }
                subs.append(d)
            return subs

        subreddit = await self.reddit.subreddit(tag)
        if random.randint(0, 1) == 0:
            time_filter = "all"
            limit = 200
        else:
            time_filter = "month"
            limit = 15

        # Length of submissions is 0 when there are 0 posts in the last month. If so, get top posts of all time.
        submissions = await getSubredditPosts(time=time_filter, post_limit=limit)
        if len(submissions) == 0:
            submissions = await getSubredditPosts(time="all", post_limit=200)

        url = None
        permalink = None
        title = None
        reps = 0
        while url is None:
            rnd = random.randint(0, len(submissions) - 1)
            if submissions[rnd]["url"][-3:] in ["jpg", "png"]:
                url = submissions[rnd]["url"]
                permalink = "https://www.reddit.com" + submissions[rnd]["permalink"]
                title = submissions[rnd]["title"]
            reps += 1
            if reps > 200:
                break

        return url, permalink, title

    @commands.command(aliases=["animal"],
                      brief="| Get cute (and not so cute) animal pictures.",
                      help=f"Supported search terms:\n"
                           f"{nl.join(accepted_terms.keys())}")
    async def img(self, ctx, *, arg=None):
        logging.info('Running image for %s', arg)
        if not arg:
            arg = random.choice(accepted_terms.keys())
        close_matches = get_close_matches(arg.lower(), accepted_terms)
        if len(close_matches) == 0:
            logging.error("No close match for %s", arg)
            await ctx.send("Could not find a good match for the search term")
        else:
            arg = str(close_matches[0])
            try:
                method = random.randint(0, 1)
                if arg in ["fatfuck", "snake"]:
                    method = 1
                if method == 0:
                    url, permalink, title = await self.getFlickrImage(arg)
                elif method == 1:
                    sub = random.choice(accepted_terms[arg])
                    url, permalink, title = await self.getRedditImage(sub)
                if url is not None:
                    embed = discord.Embed()
                    embed.description = f"[{title}]({permalink})"
                    embed.set_image(url=url)
                    await ctx.send(embed=embed)
                else:
                    logging.error("No url found")
                    await ctx.send("Could not find a url. Sorry about that :(")
            except Exception as Argument:
                logging.exception("Error occurred in img")
                await ctx.send("Error :(")


def setup(bot):
    bot.add_cog(Utility(bot))
