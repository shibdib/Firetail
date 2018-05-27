from .rss import Rss


def setup(bot):
    bot.add_cog(Rss(bot))
