from .eve_rpg import EveRpg


def setup(bot):
    bot.add_cog(EveRpg(bot))
