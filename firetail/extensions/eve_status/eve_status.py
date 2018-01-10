from discord.ext import commands

from firetail.utils import make_embed


class EveStatus:
    """This extension handles the status command."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    @commands.command(name='status', aliases=["tq", "eve"])
    async def _time(self, ctx):
        """Shows the current status of TQ."""
        self.logger.info('EveStatus - {} requested server info.'.format(str(ctx.message.author)))
        data = await ctx.bot.esi_data.server_info()
        try:
            if data.get('start_time'):
                status = 'Online'
                player_count = data.get('players')
        except Exception:
            status = 'Offline'
            player_count = 'N/A'

        embed = make_embed(guild=ctx.guild)
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot")
        embed.set_thumbnail(url="https://image.eveonline.com/Alliance/434243723_64.png")
        embed.add_field(name="Status", value="Server State:\nPlayer Count:", inline=True)
        embed.add_field(name="-", value="{}\n{}".format(status, player_count), inline=True)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()
