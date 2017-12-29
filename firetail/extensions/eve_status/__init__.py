from .eve_status import EveStatus


def setup(bot):
    bot.add_cog(EveStatus(bot))
