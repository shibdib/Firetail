from discord.ext import commands
import aiohttp
import json
import urllib

from firetail.utils import make_embed


class CharLookup:
    """This extension handles looking up characters."""

    @commands.command(name='char')
    async def _char(self, ctx):
        """Shows character information. Do '!char name'"""
        character_name = ctx.message.content.split(' ', 1)[1]
        character_id = await ctx.bot.esi_data.esi_search(character_name, 'character')
        try:
            character_data = await ctx.bot.esi_data.character_info(character_id['character'][0])
        except:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** No User Found With The Name {}'.format(character_name))
        latest_killmail, latest_system_id = await self.zkill_last_mail(character_id['character'][0])
        ship_lost_raw = await ctx.bot.esi_data.type_info_search(latest_killmail['ship_type_id'])
        ship_lost = ship_lost_raw['name']
        solar_system_info = await ctx.bot.esi_data.system_info(latest_system_id)
        solar_system_name = solar_system_info['name']
        victim_corp_raw = await ctx.bot.esi_data.corporation_info(character_data['corporation_id'])
        victim_corp = victim_corp_raw['corporation_name']
        zkill_stats = await self.zkill_stats(character_id['character'][0])
        zkill_link = 'https://zkillboard.com/character/{}/'.format(character_id['character'][0])
        eve_prism = 'http://eve-prism.com/?view=character&name={}'.format(urllib.parse.quote(character_name))
        eve_who = 'https://evewho.com/pilot/{}'.format(urllib.parse.quote(character_name))
        if zkill_stats:
            total_kills = '{0:}'.format(zkill_stats['allTimeSum'])
            danger_ratio = zkill_stats['dangerRatio']
            gang_ratio = zkill_stats['gangRatio']
            solo_kills = '{0:}'.format(zkill_stats['soloKills'])
        else:
            total_kills = 'N/A'
            danger_ratio = 'N/A'
            gang_ratio = 'N/A'
            solo_kills = 'N/A'
        try:
            victim_alliance_raw = await ctx.bot.esi_data.alliance_info(character_data['alliance_id'])
            victim_alliance = victim_alliance_raw['alliance_name']
        except:
            victim_alliance = None

        embed = make_embed(guild=ctx.guild, title_url="https://zkillboard.com/character/" + str(character_id['character'][0]) + "/",
                           title=character_data['name'], content='[ZKill]({}) / [EveWho]({}) / [EVE-Prism]({})'.format(zkill_link, eve_who, eve_prism))
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot")
        embed.set_thumbnail(url="https://imageserver.eveonline.com/Character/" + str(character_id['character'][0]) + "_64.jpg")
        if victim_alliance:
            embed.add_field(name="General Info", value='Alliance:\nCorporation:\nLast Seen Location:\nLast Seen Ship:', inline=True)
            embed.add_field(name="-", value='{}\n{}\n{}\n{}'.format(victim_alliance, victim_corp, solar_system_name, ship_lost), inline=True)
            embed.add_field(name="PVP Info", value='Threat Rating:\nGang Ratio:\nSolo Kills:\nTotal Kills:', inline=True)
            embed.add_field(name="-", value='{}%\n{}%\n{}\n{}'.format(danger_ratio, gang_ratio, solo_kills, total_kills), inline=True)
        else:
            embed.add_field(name="General Info", value='Corporation:\nLast Seen System:\nLast Seen Ship:', inline=True)
            embed.add_field(name="-", value='{}\n{}\n{}'.format(victim_corp, solar_system_name, ship_lost), inline=True)
            embed.add_field(name="PVP Info", value='Threat Rating:\nGang Ratio:\nSolo Kills:\nTotal Kills:', inline=True)
            embed.add_field(name="-", value='{}%\n{}%\n{}\n{}'.format(danger_ratio, gang_ratio, solo_kills, total_kills), inline=True)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()

    async def zkill_last_mail(self, character_id):
        async with aiohttp.ClientSession() as session:
            url = 'https://zkillboard.com/api/no-items/limit/1/characterID/{}/'.format(character_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                try:
                    victim_id = data[0]['victim']['character_id']
                except:
                    victim_id = 0
                if victim_id == character_id:
                    return data[0]['victim'], data[0]['solar_system_id']
                else:
                    for attacker in data[0]['attackers']:
                        if attacker['character_id'] == character_id:
                            return attacker, data[0]['solar_system_id']

    async def zkill_stats(self, character_id):
        async with aiohttp.ClientSession() as session:
            url = 'https://zkillboard.com/api/stats/characterID/{}/'.format(character_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                try:
                    all_time_kills = data['allTimeSum']
                    return data
                except:
                    return None
