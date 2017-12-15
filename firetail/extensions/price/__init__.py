from .price import Price


def setup(bot):
    bot.add_cog(Price(bot))
