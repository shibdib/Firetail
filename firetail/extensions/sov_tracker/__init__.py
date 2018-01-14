from .sov_tracker import SovTracker


def setup(bot):
    bot.add_cog(SovTracker(bot))
