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
        self.skip_votes = set()
        self.skipped_user = set()
        self.current_provider = set()
        self.voice = None

    @commands.command()
    async def yt(self, ctx, *, url):
        """Streams from a URL
        `!yt https://www.youtube.com/watch?v=RubBzkZzpUA` to stream audio
        `!skip` Votes to skip a song, requires 3 votes.
        `!pause` Pauses the current song.
        `!play` Resumes the current paused song.
        `!stop` to stop the current song and remove the bot from the voice channel.
        `!volume 0-100` to set the volume percentage."""

        global dest
        if ctx.author.id in self.skipped_user:
            return await dest.send('You just got skipped, let someone else pick something')

        if ctx.author.voice:
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()
            if ctx.author.voice.channel != ctx.voice_client.channel and not ctx.voice_client.is_playing():
                await ctx.author.voice.channel.move_to()
            if ctx.voice_client.is_playing():
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                return await dest.send('{} is already playing a song. You can do !skip to vote to skip this song.'.
                                       format(self.current_provider))
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
            if ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await ctx.message.delete()
            self.current_provider.clear()
            self.skipped_user.clear()
            self.skip_votes.clear()
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
        if ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        if ctx.author.id not in self.current_provider:
            return await ctx.send("ERROR: Only the person who requested the song can stop it. Try `!skip` instead.")

        self.current_provider.clear()
        self.skip_votes.clear()

        await ctx.voice_client.disconnect()
        if ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""
        if ctx.author.id not in self.current_provider:
            return await ctx.send("ERROR: Only the person who requested the song can stop it. Try `!skip` instead.")

        ctx.voice_client.pause()
        if ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()

    @commands.command()
    async def play(self, ctx):
        """Continues the current song"""

        ctx.voice_client.play()
        if ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song.
        The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """
        if not ctx.voice_client.is_playing():
            return await ctx.send('Not playing any stream_player right now... Do !yt to add a song.')

        voter = ctx.message.author
        if voter.id not in self.skip_votes:
            self.skip_votes.add(voter.id)
            total_votes = len(self.skip_votes)
            if total_votes >= 3:
                await ctx.send('Skip vote passed, stopping song.. Add a new song using `!yt`')
                self.skip_votes.clear()
                ctx.voice_client.stop()
                self.skipped_user.clear()
                self.skipped_user.add(self.current_provider)
                self.current_provider.clear()
                self.current_provider.add(ctx.author.id)
            else:
                await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))
        else:
            await ctx.send('You have already voted to skip this song.')

    async def join(self, ctx):

        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
