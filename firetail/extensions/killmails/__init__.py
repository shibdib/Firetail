from .killmails import Killmails


def setup(bot):
    bot.add_cog(Killmails(bot))
