import os
import pkgutil

from discord.ext import commands

from firetail.core import checks
from firetail import utils


class ExtensionManager:
    """Commands to add, remove and change extensions for Firetail."""

    def __local_check(self, ctx):
        return checks.check_is_co_owner(ctx)

    @commands.group()
    async def ext(self, ctx):
        """Commands to manage extensions."""
        if ctx.invoked_subcommand is None:
            await ctx.bot.send_cmd_help(ctx)

    @ext.command()
    async def list(self, ctx):
        """List all available extensions and their loaded status."""
        ext_folder = "extensions"
        ext_dir = os.path.join(os.path.dirname(__file__), "..", ext_folder)
        ext_files = [name for _, name, _ in pkgutil.iter_modules([ext_dir])]
        loaded_ext = []
        count_loaded = 0
        count_ext = 0
        msg = ""
        for ext in ctx.bot.extensions:
            loaded_ext.append(ext)
        for ext in ext_files:
            count_ext += 1
            ext_name = ("firetail.extensions."+ext)
            is_loaded = ext_name in loaded_ext
            status = ":black_small_square:"
            if is_loaded:
                count_loaded += 1
                status = ":white_small_square:"
            msg += "{0} {1}\n".format(status, ext)
        count_msg = "{} of {} extensions loaded.\n\n".format(
            count_loaded, count_ext)
        embed = utils.make_embed(msg_type='info',
                                 title='Available Extensions',
                                 content=count_msg+msg)
        await ctx.send(embed=embed)

    @ext.command()
    async def unload(self, ctx, ext):
        """Unload an extension."""
        bot = ctx.bot
        ext_name = ("firetail.extensions."+ext)
        if ext_name in bot.extensions:
            bot.unload_extension(ext_name)
            embed = utils.make_embed(msg_type='success',
                                     title=ext+' extension unloaded.')
            await ctx.send(embed=embed)
        else:
            embed = utils.make_embed(
                msg_type='error', title=ext+' extension not loaded.')
            await ctx.send(embed=embed)

    @ext.command()
    async def load(self, ctx, ext):
        """Load or reload an extension."""
        bot = ctx.bot
        ext_folder = "extensions"
        ext_dir = os.path.join(os.path.dirname(__file__), "..", ext_folder)
        ext_files = [name for _, name, _ in pkgutil.iter_modules([ext_dir])]
        if ext in ext_files:
            ext_name = ("firetail.extensions."+ext)
            was_loaded = ext_name in bot.extensions
            try:
                bot.unload_extension(ext_name)
                bot.load_extension(ext_name)
                if was_loaded:
                    msg = ext+' extension reloaded.'
                else:
                    msg = ext+' extension loaded.'
                embed = utils.make_embed(msg_type='success', title=msg)
                await ctx.send(embed=embed)
            except Exception as e:
                # logger.critical('Error loading ext: {} - {}: {}'.format(
                #    str(ext), type(e).__name__, e))
                embed = utils.make_embed(
                    msg_type='error',
                    title='Error when loading '+str(ext),
                    content='{}: {}'.format(type(e).__name__, e))
                await ctx.send(embed=embed)
        else:
            embed = utils.make_embed(
                msg_type='error',
                title=ext+' extension not found.')
            await ctx.send(embed=embed)

    @ext.command()
    async def showext(self, ctx):
        """Show raw extension list."""
        bot = ctx.bot
        embed = utils.make_embed(msg_type='info',
                                 title='Raw Extension List',
                                 content='\n'.join(bot.extensions))
        await ctx.send(embed=embed)

    @commands.command()
    async def reload_core(self, ctx):
        """Reload Core Commands."""
        bot = ctx.bot
        try:
            bot.unload_extension('firetail.core.commands')
            bot.load_extension('firetail.core.commands')
            embed = utils.make_embed(msg_type='success',
                                     title='Core Commands reloaded.')
            await ctx.send(embed=embed)
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            embed = utils.make_embed(msg_type='error',
                                     title='Error loading Core Commands',
                                     content=msg)
            await ctx.send(embed=embed)

    @commands.command()
    async def reload_dm(self, ctx):
        """Reload Data Manager."""
        bot = ctx.bot
        try:
            bot.unload_extension('firetail.data_manager')
            bot.load_extension('firetail.data_manager')
            embed = utils.make_embed(msg_type='success',
                                     title='Data Manager reloaded.')
            await ctx.send(embed=embed)
        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, e)
            embed = utils.make_embed(msg_type='error',
                                     title='Error loading Data Manager',
                                     content=msg)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ExtensionManager())