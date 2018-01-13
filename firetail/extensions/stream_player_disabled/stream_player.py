from discord.ext import commands
import discord
import asyncio
from firetail.utils import make_embed

import youtube_dl

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, ytdl.extract_info, url)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class StreamPlayer:
    """This extension handles the status command."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger
        self.song_queue = []
        self.skip_votes = set()
        self.current_provider = set()
        self.voice = None
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.tick_loop())

    async def tick_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if self.voice is not None:
                if not self.voice.is_playing():
                    song_queue = []
                    for requests in self.song_queue:
                        ctx = requests['ctx']
                        if ctx.guild.id == self.voice.guild.id:
                            song_queue.append(requests)
                    if len(song_queue) >= 1:
                        url = song_queue[0]['url']
                        ctx = song_queue[0]['ctx']
                        self.voice.stop()
                        player = await YTDLSource.from_url(url, loop=self.bot.loop)
                        count = 0
                        for requests in self.song_queue:
                            if requests['url'] == song_queue['url'] and requests['ctx'] == song_queue['ctx']:
                                self.song_queue.pop(count)
                            count = count + 1
                        self.voice.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                        self.current_provider.clear()
                        self.current_provider.add(ctx.author.id)
                        embed = make_embed(msg_type='info', title='Now playing From Queue: {}'.format(player.title),
                                           content="Requested By: {}\n[Direct Link]({})".format(ctx.author.name,
                                                                                                player.url))
                        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                                         text="Provided Via Firetail Bot")
                        dest = ctx.author if ctx.bot.config.dm_only else ctx
                        await dest.send(embed=embed)
                    else:
                        self.current_provider.clear()
                        self.skip_votes.clear()
                        self.song_queue.clear()

                        await self.voice.disconnect()
                        await asyncio.sleep(15)
                else:
                    await asyncio.sleep(60)
            else:
                await asyncio.sleep(60)

    @commands.command()
    async def yt(self, ctx, *, url):
        """Streams from a URL
        `!yt https://www.youtube.com/watch?v=RubBzkZzpUA` to stream audio
        If a song is already playing it gets added to a queue.
        `!skip` Votes to skip a song, requires 3 votes.
        `!pause` Pauses the current song.
        `!play` Resumes the current paused song.
        `!stop` to stop the current song and remove the bot from the voice channel.
        `!volume 0-100` to set the volume percentage."""

        if ctx.author.voice:
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()
            if ctx.author.voice.channel != ctx.voice_client.channel and not ctx.voice_client.is_playing():
                await ctx.author.voice.channel.move_to()
            if ctx.voice_client.is_playing():
                for request in self.song_queue:
                    if url == request['url']:
                        return await ctx.send('That song is already in the queue.')
                self.song_queue.append({"url": url, "ctx": ctx})
                embed = make_embed(msg_type='info', title='Queued: {}'.format(url))
                embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                                 text="Provided Via Firetail Bot")
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                return await dest.send(embed=embed)
            if ctx.author.voice.channel != ctx.voice_client.channel:
                await ctx.author.voice.channel.move_to()
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            embed = make_embed(msg_type='info', title='Now playing: {}'.format(player.title),
                               content="Requested By: {}\n[Direct Link]({})".format(ctx.author.name,
                                                                                    player.url))
            embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                             text="Provided Via Firetail Bot")
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            self.voice = ctx.voice_client
            await dest.send(embed=embed)
            await ctx.message.delete()
            self.current_provider.clear()
            self.current_provider.add(ctx.author.id)
        else:
            return await ctx.send("ERROR: You need to be in a voice channel to do that.")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume
        await ctx.author.send("Changed volume to {}%".format(volume))
        await ctx.message.delete()

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        self.current_provider.clear()
        self.skip_votes.clear()
        self.song_queue.clear()

        await ctx.voice_client.disconnect()
        await ctx.message.delete()

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""

        await ctx.voice_client.pause()
        await ctx.message.delete()

    @commands.command()
    async def queue(self, ctx):
        """Gets current song queue"""
        song_queue = []
        for requests in self.song_queue:
            request_ctx = requests['ctx']
            if request_ctx.guild.id == ctx.guild.id:
                song_queue.append(requests)

        if len(song_queue) > 0:
            queued = ''
            number = 0
            for song in song_queue:
                number = number + 1
                queued += str('\n{}. {}'.format(number, song['url']))
                embed = make_embed(msg_type='info', title='Current Queue',
                                   content=queued)
                embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                                 text="Provided Via Firetail Bot")
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                await dest.send(embed=embed)
        else:
            return await ctx.send('The queue is empty, add a song to the queue with the !yt command.')

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song.
        The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """
        song_queue = []
        for requests in self.song_queue:
            request_ctx = requests['ctx']
            if request_ctx.guild.id == ctx.guild.id:
                song_queue.append(requests)

        if not ctx.voice_client.is_playing():
            return await ctx.send('Not playing any stream_player right now... Do !yt to add a song.')

        if len(self.song_queue) < 1:
            return await ctx.send('The queue is empty, add a song to the queue with the !yt command.')

        voter = ctx.message.author
        if voter.id not in self.skip_votes:
            self.skip_votes.add(voter.id)
            total_votes = len(self.skip_votes)
            if total_votes >= 3 or ctx.author.id in self.current_provider:
                await ctx.send('Skip vote passed, skipping song...')
                self.skip_votes.clear()
                url = song_queue[0]['url']
                ctx = song_queue[0]['ctx']
                ctx.voice_client.stop()
                player = await YTDLSource.from_url(url, loop=self.bot.loop)
                ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
                ctx = song_queue[0]['ctx']
                count = 0
                for requests in self.song_queue:
                    if requests['url'] == song_queue['url'] and requests['ctx'] == song_queue['ctx']:
                        self.song_queue.pop(count)
                    count = count + 1
                embed = make_embed(msg_type='info', title='Now playing: {}'.format(player.title),
                                   content="Requested By: {}\n[Direct Link]({})".format(ctx.author.name,
                                                                                        player.url))
                embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                                 text="Provided Via Firetail Bot")
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                await dest.send(embed=embed)
                self.current_provider.clear()
                self.current_provider.add(ctx.author.id)
            else:
                await ctx.send('Skip vote added, currently at [{}/3]'.format(total_votes))
        else:
            await ctx.send('You have already voted to skip this song.')

    async def join(self, ctx):

        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
