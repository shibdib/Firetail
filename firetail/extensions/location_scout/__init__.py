from .location_scout import LocationScout


def setup(bot):
    bot.add_cog(LocationScout(bot))
