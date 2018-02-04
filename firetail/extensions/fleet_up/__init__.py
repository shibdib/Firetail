from .fleet_up import FleetUp


def setup(bot):
    bot.add_cog(FleetUp(bot))
