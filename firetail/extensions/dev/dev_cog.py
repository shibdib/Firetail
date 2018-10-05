import io
import os
import platform
import textwrap
import traceback
import unicodedata

from contextlib import redirect_stdout

import discord
from discord.ext import commands

from firetail import utils
from firetail.core import checks


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    # remove `foo`
    return content.strip('` \n')


def codeblock(contents, syntax="py"):
    """Returns a list of codeblock text for the given content.

    Content is broken into items with a character limitation to avoid
    going above single-message limits.
    """
    paginator = commands.Paginator(
        prefix='```{}'.format(syntax), max_size=2000)
    for line in contents.split('\n'):
        for wrapline in textwrap.wrap(line, width=1990):
            paginator.add_line(wrapline.rstrip().replace('`', '\u200b`'))
    return paginator.pages


class Dev:
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    def __local_check(self, ctx):
        """Limits all commands in the cog to only co_owners."""
        return checks.check_is_co_owner(ctx)

    @commands.command(name='eval')
    @checks.is_owner()
    async def _eval(self, ctx, *, body: str):
        """Runs and shows prints and returns of given python code."""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '__': self._last_result
        }

        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()

        to_compile = 'async def func():\n{}'.format(
            textwrap.indent(body, "  "))

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(
                '```py\n{}: {}\n```'.format(e.__class__.__name__, e))

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()

            await ctx.send('```py\n{}{}\n```'.format(
                value, traceback.format_exc()))
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except discord.Forbidden:
                pass

            if ret is None:
                if value:
                    for page in codeblock(value):
                        await ctx.send(page)
            else:
                self._last_result = ret
                for page in codeblock("{}{}".format(value, ret)):
                    await ctx.send(page)

    @commands.command()
    async def charinfo(self, ctx, *, characters: str):
        """Shows you information about unicode characters.

        Only up to 25 characters at a time.
        """
        if len(characters) > 25:
            return await ctx.send(
                'Too many characters ({}/25)'.format(len(characters)))
        charlist = []
        rawlist = []
        for char in characters:
            digit = '{0:x}'.format(ord(char))
            url = "http://www.fileformat.info/info/unicode/char/{}".format(
                digit)
            name = "[{}]({})".format(unicodedata.name(char, ''), url)
            u_code = '\\U{0:>08}'.format(digit)
            if len(str(digit)) <= 4:
                u_code = '\\u{0:>04}'.format(digit)
            charlist.append(
                ' '.join(['`{}`:'.format(u_code.ljust(10)), name, '-', char]))
            rawlist.append(u_code)

        embed = utils.make_embed(
            msg_type='info',
            title='Character Info',
            content='\n'.join(charlist))

        if len(characters) > 1:
            embed.add_field(
                name='Raw',
                value="`{}`".format(''.join(rawlist)),
                inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def runas(self, ctx, member: discord.Member, *, new_cmd):
        """Run a command as a different member."""
        if await ctx.bot.is_owner(member):
            embed = utils.make_embed(
                msg_type='error', title='No, you may not run as owner.')
            return await ctx.send(embed=embed)

        ctx.message.content = new_cmd
        ctx.message.author = member
        await ctx.bot.process_commands(ctx.message)

    @commands.command(aliases=['cls'])
    async def clear_console(self, ctx):
        """Clear the console"""
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
        await ctx.send('\u2705')

    @commands.command()
    async def hi(self, ctx):
        """Say hi. Usually a test command for doing nothing much."""
        await ctx.send("Hi {} \U0001f44b".format(ctx.author.display_name))

    @commands.command(aliases=['priv', 'privs'])
    async def privilege(self, ctx, *, member: discord.Member = None):
        """Check the bot permission level of a member."""
        member = member or ctx.author
        ctx.author = member

        def get_embed(title):
            return utils.make_embed(title=title, msg_type='info')

        if not await checks.check_is_mod(ctx):
            return await ctx.send(embed=get_embed('Normal User'))
        if not await checks.check_is_admin(ctx):
            return await ctx.send(embed=get_embed('Mod'))
        if not await checks.check_is_co_owner(ctx):
            return await ctx.send(embed=get_embed('Admin'))
        if not await checks.check_is_owner(ctx):
            return await ctx.send(embed=get_embed('Bot Co-Owner'))
        return await ctx.send(embed=get_embed('Bot Owner'))
