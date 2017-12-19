from discord.ext import commands
import aiohttp
import json
import urllib
import re
import html

from firetail.utils import make_embed


class GroupLookup:
    """This extension handles looking up corps and alliance."""

    @commands.command(name='group', aliases=["corp", "alliance"])
    async def _group(self, ctx):
        """Shows corp and alliance information. Do '!group name'"""
        group_name = ctx.message.content.split(' ', 1)[1]
        try:
            group = 'corporation'
            group_id = await ctx.bot.esi_data.esi_search(group_name, group)
            group_id = group_id['corporation'][0]
            group_data = await ctx.bot.esi_data.corporation_info(group_id)
            zkill_stats = await self.zkill_stats(group_id, 'corporationID')
            raw_corp_description = group_data['corporation_description']
            new_lines = re.sub('<br\s*?>', '\n', raw_corp_description)
            tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
            corp_description = tag_re.sub('', new_lines)
            zkill_link = 'https://zkillboard.com/corporation/{}/'.format(group_id)
            eve_who = 'https://evewho.com/corp/{}'.format(urllib.parse.quote(group_name))
            dotlan = 'http://evemaps.dotlan.net/corporation/{}'.format(urllib.parse.quote(group_name))
            logo = 'https://imageserver.eveonline.com/Corporation/{}_64.png'.format(group_id)
            try:
                alliance_id = group_data['alliance_id']
                alliance_info = await ctx.bot.esi_data.alliance_info(alliance_id)
                alliance_name = alliance_info['alliance_name']
                alliance = True
            except:
                alliance = False
        except:
            try:
                group = 'alliance'
                group_id = await ctx.bot.esi_data.esi_search(group_name, group)
                group_id = group_id['alliance'][0]
                group_data = await ctx.bot.esi_data.alliance_info(group_id)
                zkill_stats = await self.zkill_stats(group_id, 'allianceID')
                zkill_link = 'https://zkillboard.com/alliance/{}/'.format(group_id)
                eve_who = 'https://evewho.com/alli/{}'.format(urllib.parse.quote(group_name))
                dotlan = 'http://evemaps.dotlan.net/alliance/{}'.format(urllib.parse.quote(group_name))
                logo = 'https://imageserver.eveonline.com/Alliance/{}_64.png'.format(group_id)
            except:
                dest = ctx.author if ctx.bot.config.dm_only else ctx
                return await dest.send('**ERROR:** No Group Found With The Name {}'.format(group_name))
        if zkill_stats:
            total_kills = '{0:}'.format(zkill_stats['allTimeSum'])
            danger_ratio = zkill_stats['dangerRatio']
            gang_ratio = zkill_stats['gangRatio']
            solo_kills = '{0:}'.format(zkill_stats['soloKills'])
            if zkill_stats['hasSupers']:
                try:
                    super_count = len(zkill_stats['supers']['supercarriers']['data'])
                except:
                    super_count = 'N/A'
                try:
                    titan_count = len(zkill_stats['supers']['titans']['data'])
                except:
                    titan_count = 'N/A'
            else:
                super_count = 'N/A'
                titan_count = 'N/A'
            for top in zkill_stats['topLists']:
                if top['type'] == 'solarSystem':
                    most_active_system = top['values'][0]['solarSystemName']
        else:
            total_kills = 'N/A'
            danger_ratio = 'N/A'
            gang_ratio = 'N/A'
            solo_kills = 'N/A'
            super_count = 'N/A'
            titan_count = 'N/A'
            most_active_system = 'N/A'

        embed = make_embed(guild=ctx.guild,
                           title=group_name,
                           content='[ZKill]({}) / [EveWho]({}) / [Dotlan]({})'.format(zkill_link, eve_who, dotlan))
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot")
        embed.set_thumbnail(
            url=logo)
        if group == 'corporation' and alliance:
            embed.add_field(name="General Info", value='Name:\nTicker:\nMember Count:\nAlliance:',
                            inline=True)
            embed.add_field(name="-",
                            value='{}\n{}\n{}\n{}'.format(group_data['corporation_name'], group_data['ticker'], group_data['member_count'], alliance_name),
                            inline=True)
            embed.add_field(name="PVP Info", value='Threat Rating:\nGang Ratio:\nSolo Kills:\nTotal Kills:\nKnown Super Count:\nKnown Titan Count:\nMost Active System:',
                            inline=True)
            embed.add_field(name="-",
                            value='{}%\n{}%\n{}\n{}\n{}\n{}\n{}'.format(danger_ratio, gang_ratio, solo_kills, total_kills, super_count, titan_count, most_active_system),
                            inline=True)
            embed.add_field(name="Description", value=corp_description[:1023])
        elif group == 'corporation' and not alliance:
            embed.add_field(name="General Info", value='Name:\nTicker:\nMember Count:',
                            inline=True)
            embed.add_field(name="-",
                            value='{}\n{}\n{}'.format(group_data['corporation_name'], group_data['ticker'], group_data['member_count']),
                            inline=True)
            embed.add_field(name="PVP Info", value='Threat Rating:\nGang Ratio:\nSolo Kills:\nTotal Kills:\nKnown Super Count:\nKnown Titan Count:\nMost Active System:',
                            inline=True)
            embed.add_field(name="-",
                            value='{}%\n{}%\n{}\n{}\n{}\n{}\n{}'.format(danger_ratio, gang_ratio, solo_kills, total_kills, super_count, titan_count, most_active_system),
                            inline=True)
            embed.add_field(name="Description", value=corp_description[:1023])
        elif group == 'alliance':
            embed.add_field(name="General Info", value='Name:\nTicker:',
                            inline=True)
            embed.add_field(name="-",
                            value='{}\n{}'.format(group_data['alliance_name'], group_data['ticker']),
                            inline=True)
            embed.add_field(name="PVP Info", value='Threat Rating:\nGang Ratio:\nSolo Kills:\nTotal Kills:\nKnown Super Count:\nKnown Titan Count:\nMost Active System:',
                            inline=True)
            embed.add_field(name="-",
                            value='{}%\n{}%\n{}\n{}\n{}\n{}\n{}'.format(danger_ratio, gang_ratio, solo_kills, total_kills, super_count, titan_count, most_active_system),
                            inline=True)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()

    async def zkill_stats(self, group_id, group_type):
        async with aiohttp.ClientSession() as session:
            url = 'https://zkillboard.com/api/stats/{}/{}/'.format(group_type, group_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                try:
                    all_time_kills = data['allTimeSum']
                    return data
                except:
                    return None
