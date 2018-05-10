from firetail.lib import db
from firetail.utils import make_embed
import asyncio
import feedparser

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

    async def tick_loop(self):
        """ Operation loop to check for new RSS feed data while bot is active
        """
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                data = await self.poll_feeds()
                # Validate response
            except Exception:
                self.logger.exception('ERROR:')
            finally:
                await asyncio.sleep(self.updateInterval*60)

    async def poll_feeds(self):
        """ Poll a list of RSS feeds from self.config, looking for
            new content to process.
        """
        self.logger.info('Polling for new RSS feeds')
        for feed_name, feed in self.config.rss['feeds'].items():
            async with self.bot.session.get(feed['uri']) as resp:
                if resp.status != 200:
                    self.logger.error("Failed to get RSS data for feed: {}".format(feed_name))
                    break
                text = await resp.text()
                content = feedparser.parse(text)
