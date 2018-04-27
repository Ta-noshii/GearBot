import asyncio
import time
import traceback
from concurrent.futures import CancelledError
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands

from Util import GearbotLogging, VersionInfo


class BCVersionChecker:

    def __init__(self, bot):
        self.bot:commands.Bot = bot
        self.BC_VERSION_LIST = {}
        self.BCC_VERSION_LIST = {}
        self.running = True
        self.force = False
        self.bot.loop.create_task(versionChecker(self))

    def __unload(self):
        #cleanup
        self.running = False

    @commands.command()
    async def latest(self, ctx:commands.Context, version=None):
        if version is None:
            version = VersionInfo.getLatest(self.BC_VERSION_LIST.keys())
        if version not in self.BC_VERSION_LIST.keys():
            await ctx.send(f"Sorry but `{version}` does not seem to be a valid MC version that has BuildCraft releases.")
        else:
            lastestBC = VersionInfo.getLatest(self.BC_VERSION_LIST[version])

            embed = discord.Embed(title=f"Buildcraft releases", url="http://www.mod-buildcraft.com/",
                                  colour=discord.Colour(0x54d5ff), timestamp=datetime.utcfromtimestamp(time.time()))
            embed.set_thumbnail(url="https://i.imgur.com/YKGkDDZ.png")
            info = f"Buildcraft {lastestBC}\n[Changelog](https://www.mod-buildcraft.com/pages/buildinfo/BuildCraft/changelog/{lastestBC}.html) | [Blog]({lastestBC['blog_entry'] if 'blog_entry' in lastestBC else 'https://www.mod-buildcraft.com'}) | [Direct download](https://mod-buildcraft.com/releases/BuildCraft/{lastestBC}/buildcraft-{lastestBC}.jar)"

            embed.add_field(name=f"Latest BuildCraft releases for {version}:", value=info)

            await ctx.send(embed=embed)

            if version in self.BCC_VERSION_LIST.keys():
                latestBCC = VersionInfo.getLatest(self.BCC_VERSION_LIST[version])







def setup(bot):
    bot.add_cog(BCVersionChecker(bot))

async def versionChecker(checkcog:BCVersionChecker):
    while not checkcog.bot.STARTUP_COMPLETE:
        await asyncio.sleep(1)
    GearbotLogging.info("Started BC version checking background task")
    session:aiohttp.ClientSession
    reply:aiohttp.ClientResponse
    lastUpdate = 0
    async with aiohttp.ClientSession() as session:
        while checkcog.running:
            try:
                async with session.get('https://www.mod-buildcraft.com/build_info_full/last_change.txt') as reply:
                    stamp = await reply.text()
                    stamp = int(stamp[:-1])
                    if stamp > lastUpdate:
                        GearbotLogging.info("New BC version somewhere!")
                        lastUpdate = stamp
                        checkcog.BC_VERSION_LIST = await getList(session, "BuildCraft")
                        checkcog.BCC_VERSION_LIST = await getList(session, "BuildCraftCompat")
                        highestMC = VersionInfo.getLatest(checkcog.BC_VERSION_LIST.keys())
                        latestBC = VersionInfo.getLatest(checkcog.BC_VERSION_LIST[highestMC])
                        generalID = 309218657798455298
                        channel:discord.TextChannel = checkcog.bot.get_channel(generalID)
                        if channel is not None and latestBC not in channel.topic:
                            async with session.get(f'https://www.mod-buildcraft.com/build_info_full/BuildCraft/{latestBC}.json') as reply:
                                info = await reply.json()
                                newTopic = f"General discussions about BuildCraft.\n" \
                                           f"Latest version: {latestBC}\n" \
                                           f"Full changelog and download: {info['blog_entry']}"
                                await channel.edit(topic=newTopic)
                        pass
                    pass
            except CancelledError:
                pass  # bot shutdown
            except Exception as ex:
                checkcog.bot.errors = checkcog.bot.errors + 1
                GearbotLogging.error("Something went wrong in the BC version checker task")
                GearbotLogging.error(traceback.format_exc())
                embed = discord.Embed(colour=discord.Colour(0xff0000),
                                      timestamp=datetime.utcfromtimestamp(time.time()))

                embed.set_author(name="Something went wrong in the BC version checker task:")
                embed.add_field(name="Exception", value=ex)
                v = ""
                for line in traceback.format_exc().splitlines():
                    if len(v) + len(line) > 1024:
                        embed.add_field(name="Stacktrace", value=v)
                        v = ""
                    v = f"{v}\n{line}"
                if len(v) > 0:
                    embed.add_field(name="Stacktrace", value=v)
                await GearbotLogging.logToBotlog(embed=embed)
            for i in range(1,60):
                if checkcog.force or not checkcog.running:
                    break
                await asyncio.sleep(10)

    GearbotLogging.info("BC version checking background task terminated")


async def getList(session, link):
    async with session.get(f"https://www.mod-buildcraft.com/build_info_full/{link}/versions.json") as reply:
        list = await reply.json()
        if "unknown" in list.keys():
            del list["unknown"]
        return list