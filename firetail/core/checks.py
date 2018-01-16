import discord
import time
from discord.ext import commands


async def check_is_owner(ctx):
    return await ctx.bot.is_owner(ctx.author)


async def check_is_co_owner(ctx):
    owner = ctx.author.id in ctx.bot.co_owners
    co_owner = await ctx.bot.is_owner(ctx.author)
    return owner or co_owner


async def check_is_admin(ctx):
    return ctx.author.guild_permissions.administrator


async def check_is_mod(ctx):
    return ctx.channel.permissions_for(ctx.author).manage_messages


async def check_spam(ctx):
    if '!help' in ctx.message.content:
        return True
    spam_list = ctx.bot.bot_users
    spam_list_length = len(spam_list)
    spam_list.append(ctx.author.id)
    if ctx.bot.last_command is not None:
        if spam_list_length >= 5:
            iterations = int((time.time() - ctx.bot.last_command) / 5)
            if iterations > spam_list_length:
                iterations = spam_list_length - 1
            x = 0
            while x < iterations:
                spam_list.pop(0)
                x += 1
        if len(ctx.bot.repeat_offender) >= 3:
            iterations = int((time.time() - ctx.bot.last_command) / 30)
            if iterations > spam_list_length:
                iterations = spam_list_length - 1
            x = 0
            while x < iterations:
                ctx.bot.repeat_offender.pop(0)
                x += 1
    ctx.bot.last_command = time.time()
    repeat = ctx.bot.repeat_offender.count(ctx.author.id)
    if repeat >= 3:
        wait_time = int((repeat - 2) * 30)
        if ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()
            await ctx.author.send('WARNING: You are being rate limited from using bot commands.'
                                  ' Try again in {} seconds'.
                                  format(wait_time))
        else:
            await ctx.author.send('WARNING: You are being rate limited from using bot commands.'
                                  ' Try again in {} seconds'.
                                  format(wait_time))
        ctx.bot.repeat_offender.append(ctx.author.id)
        return False
    spam_count = spam_list.count(ctx.author.id)
    low_threshold = 0.75 * spam_list_length
    threshold = 0.45 * spam_list_length
    if (spam_list_length >= 5 and spam_count > low_threshold) or (spam_list_length >= 10 and spam_count > threshold):
        wait_time = int((spam_count - threshold) * 5)
        if ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.message.delete()
            await ctx.author.send('WARNING: You are being rate limited from using bot commands.'
                                  ' Try again in {} seconds'.
                                  format(wait_time))
        else:
            await ctx.author.send('WARNING: You are being rate limited from using bot commands.'
                                  ' Try again in {} seconds'.
                                  format(wait_time))
        ctx.bot.repeat_offender.append(ctx.author.id)
        return False
    if spam_list_length >= 40:
        spam_list.pop(0)
    return True


def is_owner():
    return commands.check(check_is_owner)


def is_co_owner():
    return commands.check(check_is_co_owner)


def is_admin():
    return commands.check(check_is_admin)


def is_mod():
    return commands.check(check_is_mod)


def spam_check():
    return commands.check(check_spam)


async def check_permissions(ctx, perms):
    if await ctx.bot.is_owner(ctx.author):
        return True
    elif not perms:
        return False
    resolved = ctx.channel.permissions_for(ctx.author)

    return all(getattr(resolved, name, None) == value for name, value in perms.items())


def mod_or_permissions(**perms):
    async def predicate(ctx):
        has_perms_or_is_owner = await check_permissions(ctx, perms)
        if ctx.guild is None:
            return has_perms_or_is_owner
        author = ctx.author
        # settings = ctx.bot.db.guild(ctx.guild)
        # mod_role_id = await settings.mod_role()
        # admin_role_id = await settings.admin_role()

        mod_role = discord.utils.get(ctx.guild.roles)  # , id=mod_role_id
        admin_role = discord.utils.get(ctx.guild.roles)  # , id=admin_role_id

        is_staff = mod_role in author.roles or admin_role in author.roles
        is_guild_owner = author == ctx.guild.owner

        return is_staff or has_perms_or_is_owner or is_guild_owner

    return commands.check(predicate)


def admin_or_permissions(**perms):
    async def predicate(ctx):
        has_perms_or_is_owner = await check_permissions(ctx, perms)
        if ctx.guild is None:
            return has_perms_or_is_owner
        author = ctx.author
        is_guild_owner = author == ctx.guild.owner
        # admin_role_id = await ctx.bot.db.guild(ctx.guild).admin_role()
        admin_role = discord.utils.get(ctx.guild.roles)  # , id=admin_role_id

        return admin_role in author.roles or has_perms_or_is_owner or is_guild_owner

    return commands.check(predicate)


def guildowner_or_permissions(**perms):
    async def predicate(ctx):
        has_perms_or_is_owner = await check_permissions(ctx, perms)
        if ctx.guild is None:
            return has_perms_or_is_owner
        is_guild_owner = ctx.author == ctx.guild.owner

        return is_guild_owner or has_perms_or_is_owner

    return commands.check(predicate)


def guildowner():
    return guildowner_or_permissions()


def admin():
    return admin_or_permissions()


def mod():
    return mod_or_permissions()


def is_prefix(*args):
    def check(ctx):
        prefix = ctx.prefix
        return prefix in args

    return commands.check(check)
