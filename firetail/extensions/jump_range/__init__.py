from .jump_range import JumpRange


def setup(bot):
    bot.add_cog(JumpRange(bot))
