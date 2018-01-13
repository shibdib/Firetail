from .stream_player import StreamPlayer


def setup(bot):
    bot.add_cog(StreamPlayer(bot))
