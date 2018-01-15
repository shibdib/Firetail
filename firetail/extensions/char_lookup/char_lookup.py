from discord.ext import commands
from statistics import mode
import aiohttp
import json
import urllib

from firetail.utils import make_embed


class CharLookup:
    """This extension handles looking up characters."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.logger = bot.logger

    @commands.command(name='char')
    async def _char(self, ctx):
        """Shows character information.
        Do '!char name'"""
        if len(ctx.message.content.split()) == 1:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            return await dest.send('**ERROR:** Use **!help char** for more info.')
        character_name = ctx.message.content.split(' ', 1)[1]
        self.logger.info(
            'CharLookup - {} requested character info for the user {}'.format(str(ctx.message.author), character_name))
        character_id = await ctx.bot.esi_data.esi_search(character_name, 'character')
        try:
            if len(character_id['character']) > 1:
                for id in character_id['character']:
                    character_data = await ctx.bot.esi_data.character_info(id)
                    if character_data['name'].lower().strip().replace("'",
                                                                      '1') == character_name.lower().strip().replace(
                            "'", '1'):
                        character_id = id
                        character_data = await ctx.bot.esi_data.character_info(character_id)
                        character_name = character_data['name']
                        break
            else:
                character_id = character_id['character'][0]
                character_data = await ctx.bot.esi_data.character_info(character_id)
                character_name = character_data['name']
        except Exception:
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            self.logger.info('CharLookup ERROR - {} could not be found'.format(character_name))
            return await dest.send('**ERROR:** No User Found With The Name {}'.format(character_name))
        latest_killmail, latest_system_id = await self.zkill_last_mail(character_id)
        ship_lost = 'No Killmails Found'
        solar_system_name = 'N/A'
        if latest_killmail is not None:
            ship_lost_raw = await ctx.bot.esi_data.type_info_search(latest_killmail['ship_type_id'])
            ship_lost = ship_lost_raw['name']
            solar_system_info = await ctx.bot.esi_data.system_info(latest_system_id)
            solar_system_name = solar_system_info['name']
        victim_corp_raw = await ctx.bot.esi_data.corporation_info(character_data['corporation_id'])
        victim_corp = victim_corp_raw['name']
        zkill_stats = await self.zkill_stats(character_id)
        firetail_intel = await self.firetail_intel(character_id, character_name, zkill_stats)
        zkill_link = 'https://zkillboard.com/character/{}/'.format(character_id)
        eve_prism = 'http://eve-prism.com/?view=character&name={}'.format(urllib.parse.quote(character_name))
        eve_who = 'https://evewho.com/pilot/{}'.format(urllib.parse.quote(character_name))
        try:
            if zkill_stats['allTimeSum']:
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
                victim_alliance = victim_alliance_raw['name']
            except Exception:
                victim_alliance = None

            embed = make_embed(guild=ctx.guild,
                               title_url="https://zkillboard.com/character/" + str(character_id) + "/",
                               title=character_data['name'],
                               content='[ZKill]({}) / [EveWho]({}) / [EVE-Prism]({})'.format(zkill_link, eve_who,
                                                                                             eve_prism))
            embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                             text="Provided Via Firetail Bot")
            embed.set_thumbnail(
                url="https://imageserver.eveonline.com/Character/" + str(character_id) + "_64.jpg")
            if victim_alliance:
                embed.add_field(name="Firetail Intel Report", value=firetail_intel,
                                inline=False)
                embed.add_field(name="General Info",
                                value='Alliance:\nCorporation:\nLast Seen Location:\nLast Seen Ship:',
                                inline=True)
                embed.add_field(name="-",
                                value='{}\n{}\n{}\n{}'.format(victim_alliance, victim_corp, solar_system_name,
                                                              ship_lost),
                                inline=True)
                embed.add_field(name="PVP Info", value='Threat Rating:\nGang Ratio:\nSolo Kills:\nTotal Kills:',
                                inline=True)
                embed.add_field(name="-",
                                value='{}%\n{}%\n{}\n{}'.format(danger_ratio, gang_ratio, solo_kills, total_kills),
                                inline=True)
            else:
                embed.add_field(name="Firetail Intel Report", value=firetail_intel,
                                inline=False)
                embed.add_field(name="General Info", value='Corporation:\nLast Seen System:\nLast Seen Ship:',
                                inline=True)
                embed.add_field(name="-", value='{}\n{}\n{}'.format(victim_corp, solar_system_name, ship_lost),
                                inline=True)
                embed.add_field(name="PVP Info", value='Threat Rating:\nGang Ratio:\nSolo Kills:\nTotal Kills:',
                                inline=True)
                embed.add_field(name="-",
                                value='{}%\n{}%\n{}\n{}'.format(danger_ratio, gang_ratio, solo_kills, total_kills),
                                inline=True)
            dest = ctx.author if ctx.bot.config.dm_only else ctx
            await dest.send(embed=embed)
            if ctx.bot.config.delete_commands:
                await ctx.message.delete()
        except Exception:
            try:
                victim_alliance_raw = await ctx.bot.esi_data.alliance_info(character_data['alliance_id'])
                victim_alliance = victim_alliance_raw['name']
            except Exception:
                victim_alliance = None

            embed = make_embed(guild=ctx.guild,
                               title_url="https://zkillboard.com/character/" + str(character_id) + "/",
                               title=character_data['name'],
                               content='[ZKill]({}) / [EveWho]({}) / [EVE-Prism]({})'.format(zkill_link, eve_who,
                                                                                             eve_prism))
            embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                             text="Provided Via Firetail Bot")
            embed.set_thumbnail(
                url="https://imageserver.eveonline.com/Character/" + str(character_id) + "_64.jpg")
            if victim_alliance:
                embed.add_field(name="Firetail Intel Report", value=firetail_intel,
                                inline=False)
                embed.add_field(name="General Info",
                                value='Alliance:\nCorporation:\nLast Seen Location:\nLast Seen Ship:',
                                inline=True)
                embed.add_field(name="-",
                                value='{}\n{}\n{}\n{}'.format(victim_alliance, victim_corp, solar_system_name,
                                                              ship_lost),
                                inline=True)
            else:
                embed.add_field(name="Firetail Intel Report", value=firetail_intel,
                                inline=False)
                embed.add_field(name="General Info", value='Corporation:\nLast Seen System:\nLast Seen Ship:',
                                inline=True)
                embed.add_field(name="-", value='{}\n{}\n{}'.format(victim_corp, solar_system_name, ship_lost),
                                inline=True)
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
                except Exception:
                    victim_id = 0
                try:
                    if victim_id == character_id:
                        return data[0]['victim'], data[0]['solar_system_id']
                    else:
                        for attacker in data[0]['attackers']:
                                if attacker['character_id'] == character_id:
                                    return attacker, data[0]['solar_system_id']
                except Exception:
                    return None, None

    async def zkill_stats(self, character_id):
        async with aiohttp.ClientSession() as session:
            url = 'https://zkillboard.com/api/stats/characterID/{}/'.format(character_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                try:
                    all_time_kills = data['allTimeSum']
                    return data
                except Exception:
                    return None

    async def firetail_intel(self, character_id, character_name, zkill_stats):
        try:
            solo = 100 - zkill_stats['gangRatio']
            threat = zkill_stats['dangerRatio']
            character_type, special = await self.character_type(character_id, solo, threat)
            top_lists = zkill_stats['topLists']
            for top_type in top_lists:
                if top_type['type'] == 'solarSystem':
                    try:
                        top_system = 'The past week they have been most active in {}'.format(
                            top_type['values'][0]['solarSystemName'])
                    except Exception:
                        top_system = 'This player has not been active recently'
            intel = '{}\n{} is most likely a {}. {}. You have a {}%' \
                    ' chance of encountering this player solo.'.format(special, character_name, character_type,
                                                                       top_system, solo)
            return intel
        except Exception:
            loss_url = 'https://zkillboard.com/api/kills/characterID/{}/losses/limit/20/no-attackers/'.format(
                character_id)
            kill_url = 'https://zkillboard.com/api/kills/characterID/{}/kills/limit/1/no-items/'.format(character_id)
            solo = 0
            threat = 0
            character_type, special = await self.character_type(character_id, solo, threat)
            intel = '{}\n{} is most likely a {}. No further intel available at this time.'.format(special,
                                                                                                  character_name,
                                                                                                  character_type)
            return intel

    async def character_type(self, character_id, solo, threat):
        titans = [11567, 3764, 671, 23773, 42126, 42241, 45649]
        supers = [23919, 23917, 23913, 22852, 3514, 42125]
        probe_launchers = [4258, 4260, 17901, 17938, 28756, 28758]
        loss_url = 'https://zkillboard.com/api/kills/characterID/{}/losses/limit/20/no-attackers/'.format(
            character_id)
        kill_url = 'https://zkillboard.com/api/kills/characterID/{}/kills/limit/1/no-items/'.format(character_id)
        covert_cyno = 0
        cyno = 0
        probes = 0
        lost_ship_type_id = 0
        special = ' '
        last_kill = await self.last_kill(kill_url)
        try:
            for attacker in last_kill['attackers']:
                if attacker['character_id'] == character_id:
                    if attacker['ship_type_id'] in titans:
                        special = '**This pilot has been seen in a Titan\n**'
                    elif attacker['ship_type_id'] in supers:
                        special = '**This pilot has been seen in a Super\n**'
                    else:
                        special = ' '
        except Exception:
            special = ' '
        async with aiohttp.ClientSession() as session:
            async with session.get(loss_url) as resp:
                data = await resp.text()
                data = json.loads(data)
                for loss in data:
                    for item in loss['victim']['items']:
                        if item['item_type_id'] == 28646:
                            covert_cyno = covert_cyno + 1
                        elif item['item_type_id'] == 21096:
                            cyno = cyno + 1
                        elif item['item_type_id'] in probe_launchers:
                            probes = probes + 1
                    lost_ship_type_id = loss['victim']['ship_type_id']
                if covert_cyno >= 2:
                    try:
                        attackers = last_kill['attackers']
                    except Exception:
                        return '**BLOPS Hotdropper**', special
                    alliance_ids = []
                    corporation_ids = []
                    for attacker in last_kill['attackers']:
                        try:
                            alliance_ids.append(attacker['alliance_id'])
                            corporation_ids.append(attacker['corporation_id'])
                        except Exception:
                            corporation_ids.append(attacker['corporation_id'])
                    try:
                        dominant_alliance = mode(alliance_ids)
                        alliance_raw = await self.bot.esi_data.alliance_info(dominant_alliance)
                        alliance = alliance_raw['name']
                        return '**BLOPS Hotdropper for {}**'.format(alliance), special
                    except Exception:
                        dominant_corp = mode(corporation_ids)
                        corp_raw = await self.bot.esi_data.corporation_info(dominant_corp)
                        corp = corp_raw['name']
                        return '**BLOPS Hotdropper for {}**'.format(corp), special
                if cyno >= 5 and (threat <= 30 or threat == 0):
                    return 'Cyno Alt', special
                if probes >= 5 and threat >= 51:
                    return '**Combat Prober / Possible FC**', special
                if probes >= 5 and (threat <= 50 or threat == 0):
                    return 'Exploration Pilot', special
                if cyno >= 5 and threat >= 31:
                    return '**Possible Hot Dropper**', special
                if threat <= 30 and lost_ship_type_id == 28352:
                    return 'Rorqual Pilot', special
                if threat <= 30:
                    return 'PVE Pilot', special
                if solo >= 50:
                    return 'Solo PVP Pilot', special
                if solo <= 15:
                    return 'Fleet Pilot', special
                if solo <= 49:
                    return 'Balanced PVP Pilot', special

    async def last_kill(self, kill_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(kill_url) as resp:
                data = await resp.text()
                data = json.loads(data)
                try:
                    all_time_kills = data[0]['killmail_id']
                    return data[0]
                except Exception:
                    return None
