from firetail.lib import db
from discord.ext import commands
from firetail.core import checks
import asyncio
import feedparser
import discord
from datetime import datetime

class Rss:
    # Number of minutes between feed checks
    DEFAULT_UPDATE_INTERVAL = 15

    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.config = bot.config
        self.logger = bot.logger
        self.logger.info(self.session)
        self.loop = asyncio.get_event_loop()
        self.updateInterval = self.config.rss.get(
            'updateInterval',
            self.DEFAULT_UPDATE_INTERVAL)
        self.loop.create_task(self.tick_loop())

    @commands.command(name='setRss')
    @checks.is_mod()
    async def _set_rss(self, ctx):
        """Sets a channel to receive eve related RSS updates.
        Do **!setRss dev** to have a channel relay dev posts.
        Do **!setRss eve** to have a channel relay general ccp posts.
        Do **!setRss all** to have a channel relay both posts."""
        feed = ctx.message.content.split(' ', 1)[1]
        if feed.lower() is 'dev':
            feeds = 1
            text = 'receive CCP Dev posts.'
        elif feed.lower() is 'eve':
            feeds = 2
            text = 'receive EVE Online posts.'
        else:
            feeds = 3
            text = 'receive CCP Dev Blogs and EVE Online posts.'
        sql = ''' REPLACE INTO rss_channels(rss_feed,channel_id)
                  VALUES(?,?) '''
        channel = ctx.message.channel.id
        values = (channel, feeds)
        await db.execute_sql(sql, values)
        self.logger.info('eve_rss - {} added {} to the rpg channel list.')
        return await ctx.author.send('**Success** - Channel added to {}.'.format(text))

    @commands.command(name='deleteRss')
    @checks.is_mod()
    async def _delete_rss(self, ctx):
        """Un-sets a channel as an RSS channel."""
        sql = ''' DELETE FROM rss_channels WHERE `channel_id` = (?) '''
        values = (ctx.message.channel.id,)
        await db.execute_sql(sql, values)
        self.logger.info('eve_rss - {} removed {} from the rpg channel list.')
        return await ctx.author.send('**Success** - Channel removed.')

    async def tick_loop(self):
        """ Operation loop to check for new RSS feed data while bot is active
        """
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                data = await self.poll_feeds()
                sendable_entries = await self.find_new_entries(data)
                await self.send_and_record(sendable_entries)
            except Exception:
                self.logger.exception('ERROR:')
            finally:
                await asyncio.sleep(self.updateInterval*60)

    async def poll_feeds(self):
        """ Poll a list of RSS feeds from self.config, looking for
            new content to process.

        Returns:
            feeds - Dict of { feed_name: feedparser.parse } results
        """
        self.logger.info('Polling for new RSS feeds')
        feeds = {}
        for feed_name, feed in self.config.rss['feeds'].items():
            async with self.bot.session.get(feed['uri']) as resp:
                if resp.status != 200:
                    self.logger.error("Failed to get RSS data for feed: {}".format(feed_name))
                    break
                text = await resp.text()
                content = feedparser.parse(text)
                feeds[feed_name] = content
        return feeds

    async def find_new_entries(self, feeds):
        """ Process a dict of feedparser feeds, determining new entries
        to be processed

        Parameters:
            feeds - Dict of { feed_name: feedparser.parse } results

        Returns:
            Dict of { feed_name: feedparser.parse } with only entries to be sent
        """
        sendable_feeds = {}
        for feed_name, feed in feeds.items():
            sendable_entries = []
            for entry in feed['entries']:
                posted = await db.select_var(
                        'SELECT channel_id FROM rss where entry_id = ?',
                        (entry['id'],))  # one-entry tuple
                if posted != None and not posted:
                    sendable_entries.append(entry)
                else:
                    self.logger.debug("Entry {} already processed".format(entry['id']))
            else:
                self.logger.info("Found {} new entries for feed {}".format(
                    len(sendable_entries), feed_name))
                sendable_feed = feed
                sendable_feed['entries'] = sendable_entries
                sendable_feeds[feed_name] = sendable_feed
        return sendable_feeds

    def format_message(self, feed_title, entry):
        timestamp = datetime.strptime(entry['published'],
                                      '%a, %d %b %Y %H:%M:%S %Z')
        embed = discord.Embed(title=entry['title'],
                              timestamp=timestamp,
                              url=entry['link'])
        embed.set_author(name=entry.get('author', ''))
        return ("New post by {}".format(feed_title), embed)

    async def send_and_record(self, feeds):
        """ Send feed entries messages to the required channels, and record
        successfull sends to the DB

        Parameters:
            feeds - Dict of { feed_name: feedparser.parse } results
        """
        for feed_name, feed in feeds.items():
            channel_id = self.config.rss.get('channelId', None)
            # Try to overwrite channel_id using a feed specific channel
            channel_id = self.config.rss['feeds'][feed_name].get('channelId', channel_id)
            try:
                channel = self.bot.get_channel(int(channel_id))
                self.logger.debug("Sending to channel {} for feed {}".format(
                    channel_id, feed_name))
            except Exception:
                self.logger.exception("Bad channel {} for feed {}".format(
                    channel_id, feed_name))
                break
            # Start sending entries
            for entry in feed['entries']:
                content, embed = self.format_message(feed['feed']['title'], entry)
                try:
                    await channel.send(content, embed=embed)
                except Exception:
                    self.logger.exception("Failed to send {} to channel {} for feed {}".format(
                        entry['id'], channel_id, feed_name))
                else:
                    sql = '''REPLACE INTO rss(entry_id,channel_id) VALUES(?,?)'''
                    values = (entry['id'], channel_id)
                    try:
                        await db.execute_sql(sql, values)
                    except Exception:
                        self.logger.exception("Failed to store sending of entry {}".format(entry['id']))
            sql = "SELECT * FROM rss_channels"
            other_channels = await db.select(sql)
            for rss_channels in other_channels:
                #  Check if channels are still good and remove if not
                channel_id = int(rss_channels[2])
                channel = self.bot.get_channel(int(rss_channels[2]))
                if channel is None:
                    continue
                if feed_name.lower() is 'evenews':
                    if rss_channels[2] is 2 or 3:
                        # Start sending entries
                        for entry in feed['entries']:
                            content, embed = self.format_message(feed['feed']['title'], entry)
                            try:
                                await channel.send(content, embed=embed)
                            except Exception:
                                self.logger.exception("Failed to send {} to channel {} for feed {}".format(
                                    entry['id'], channel_id, feed_name))
                            else:
                                sql = '''REPLACE INTO rss(entry_id,channel_id) VALUES(?,?)'''
                                values = (entry['id'], channel_id)
                                try:
                                    await db.execute_sql(sql, values)
                                except Exception:
                                    self.logger.exception("Failed to store sending of entry {}".format(entry['id']))
                elif feed_name.lower() is 'evedev':
                    if rss_channels[2] is 1 or 3:
                        # Start sending entries
                        for entry in feed['entries']:
                            content, embed = self.format_message(feed['feed']['title'], entry)
                            try:
                                await channel.send(content, embed=embed)
                            except Exception:
                                self.logger.exception("Failed to send {} to channel {} for feed {}".format(
                                    entry['id'], channel_id, feed_name))
                            else:
                                sql = '''REPLACE INTO rss(entry_id,channel_id) VALUES(?,?)'''
                                values = (entry['id'], channel_id)
                                try:
                                    await db.execute_sql(sql, values)
                                except Exception:
                                    self.logger.exception("Failed to store sending of entry {}".format(entry['id']))