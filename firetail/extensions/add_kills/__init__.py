from .add_kills import AddKills


def setup(bot):
    bot.add_cog(AddKills(bot))
