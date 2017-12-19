from discord.ext import commands
import aiohttp
import json

from firetail.utils import make_embed


class CharLookup:
    """This extension handles looking up characters."""

    @commands.command(name='char')
    async def _char(self, ctx):
        """Shows character information. Do '!char name'"""
        character_name = ctx.message.content.split(' ', 1)[1]
        character_id = await ctx.bot.esi_data.esi_search(character_name, 'character')
        character_data = await ctx.bot.esi_data.character_info(character_id['character'][0])
        latest_killmail, latest_system_id = await self.zkill_info(character_id['character'][0])
        ship_lost_raw = await ctx.bot.esi_data.type_info_search(latest_killmail['ship_type_id'])
        ship_lost = ship_lost_raw['name']
        solar_system_info = await ctx.bot.esi_data.system_info(latest_system_id)
        solar_system_name = solar_system_info['name']
        victim_corp_raw = await ctx.bot.esi_data.corporation_info(character_data['corporation_id'])
        victim_corp = victim_corp_raw['corporation_name']
        try:
            victim_alliance_raw = await ctx.bot.esi_data.alliance_info(character_data['alliance_id'])
            victim_alliance = victim_alliance_raw['alliance_name']
        except:
            victim_alliance = None

        embed = make_embed(guild=ctx.guild, title_url="https://zkillboard.com/character/" + str(character_id['character'][0]) + "/",
                           title=character_data['name'], content='Character Info:')
        embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                         text="Provided Via Firetail Bot")
        embed.set_thumbnail(url="https://imageserver.eveonline.com/Character/" + str(character_id['character'][0]) + "_64.png")
        if victim_alliance:
            embed.add_field(name="Info", value='Alliance:\nCorporation:\nLast Seen Location:\nLast Seen Ship:', inline=True)
            embed.add_field(name="Test", value='{}\n{}\n{}\n{}'.format(victim_alliance, victim_corp, solar_system_name,
                                                                       ship_lost), inline=True)
        else:
            embed.add_field(name="Info", value='Corporation:\nLast Seen System:\nLast Seen Ship:', inline=True)
            embed.add_field(name="Test", value='{}\n{}\n{}'.format(victim_corp, solar_system_name, ship_lost), inline=True)
        dest = ctx.author if ctx.bot.config.dm_only else ctx
        await dest.send(embed=embed)
        if ctx.bot.config.delete_commands:
            await ctx.message.delete()

    async def zkill_info(self, character_id):
        async with aiohttp.ClientSession() as session:
            url = 'https://zkillboard.com/api/no-items/kills/limit/1/characterID/{}/'.format(character_id)
            async with session.get(url) as resp:
                data = await resp.text()
                data = json.loads(data)
                if data[0]['victim']['character_id'] == character_id: # TODO fix for structure kills
                    return data[0]['victim'], data[0]['solar_system_id']
                else:
                    for attacker in data[0]['attackers']:
                        if attacker['character_id'] == character_id:
                            return attacker, data[0]['solar_system_id']
