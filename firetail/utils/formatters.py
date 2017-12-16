import discord


def colour(*args):
    """Returns a discord Colour object.
    Pass one as an argument to define colour:
        `str` match common colour names.
        `discord.Guild` bot's guild colour.
        `None` light grey.
    """
    arg = args[0] if args else None
    if isinstance(arg, str):
        colour = arg
        try:
            return getattr(discord.Colour, colour)()
        except AttributeError:
            return discord.Colour.lighter_grey()
    if isinstance(arg, discord.Guild):
        return arg.me.colour
    else:
        return discord.Colour.lighter_grey()


def make_embed(msg_type='', title=None, title_url=None, icon=None,
               content=None, msg_colour=None, guild=None):
    """Returns a formatted discord embed object.

    Define either a type or a colour, not both.
    Types are:
    error, warning, info, success.
    """
    embed_types = {
        'error': {
            'icon': 'https://i.imgur.com/juhq2uJ.png',
            'colour': 'red'
        },
        'warning': {
            'icon': 'https://i.imgur.com/4JuaNt9.png',
            'colour': 'gold'
        },
        'info': {
            'icon': 'https://i.imgur.com/wzryVaS.png',
            'colour': 'blue'
        },
        'success': {
            'icon': 'https://i.imgur.com/ZTKc3mr.png',
            'colour': 'green'
        },
        'help': {
            'icon': 'https://i.imgur.com/kTTIZzR.png',
            'colour': 'blue'
        }
    }
    if msg_type in embed_types.keys():
        msg_colour = embed_types[msg_type]['colour']
        icon = embed_types[msg_type]['icon']
    if guild and not msg_colour:
        msg_colour = colour(guild)
    else:
        msg_colour = colour(msg_colour)
    embed = discord.Embed(description=content, colour=msg_colour)
    if not title_url:
        title_url = discord.Embed.Empty
    if not icon:
        icon = discord.Embed.Empty
    if title:
        embed.set_author(name=title, icon_url=icon, url=title_url)
    return embed