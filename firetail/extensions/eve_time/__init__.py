from .eve_time import EveTime


def setup(bot):
    bot.add_cog(EveTime(bot))
