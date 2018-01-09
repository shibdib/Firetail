from .recon import Recon


def setup(bot):
    bot.add_cog(Recon(bot))
