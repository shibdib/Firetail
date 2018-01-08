from .jump_planner import JumpPlanner


def setup(bot):
    bot.add_cog(JumpPlanner(bot))
