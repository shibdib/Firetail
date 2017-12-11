from lib import esi
import urllib.request
import json
import discord


async def run(client, logger, config):
    #  Get latest kill data
    data = redis(client)
    #  Foreach thru all provided groups
    for group in config.PluginSettings.killmail:
        killmail_group_id = group['id']
        channel_id = group['channelId']
        loss = group['lossMails']
        #  Get all group id's from the mail
        group_ids = []
        for parties in data['killmail']:
            if loss:
                for groups in parties['victim']:
                    group_ids.append(int(groups['corporation_id']))
                    group_ids.append(int(groups['alliance_id']))
            for groups in parties['attackers']:
                group_ids.append(int(groups['corporation_id']))
                group_ids.append(int(groups['alliance_id']))
        if killmail_group_id in group_ids:
            kill_id = data['killID']
            value_raw = data['zkb']['totalValue']
            victim_id = data['killmail']['victim']['character_id']
            victim_name = esi.character_name(victim_id)
            ship_lost_id = data['killmail']['victim']['ship_type_id']
            ship_lost = esi.type_info_search(ship_lost_id)['name']
            victim_corp_id = data['killmail']['victim']['corporation_id']
            victim_corp = esi.corporation_info(victim_corp_id)['corporation_name']
            victim_alliance_id = data['killmail']['victim']['alliance_id']
            victim_alliance = esi.alliance_info(victim_alliance_id)['alliance_name']
            solar_system_id = data['killmail']['solar_system_id']
            solar_system = esi.esi_search(solar_system_id, 'solarSystem')
            title = victim_name + " Lost a " + ship_lost + " Valued At " + value_raw + " ISK "
            em = discord.Embed(title=title.title(), description="Fight Occurred In: " + str(solar_system),
                               url="https://zkillboard.com/kill/" + str(kill_id) + "/", colour=0xDEADBF)
            em.set_footer(icon_url=client.user.default_avatar_url, text="Provided Via Firetail Bot + ZKill")
            em.set_thumbnail(url="https://image.eveonline.com/Type/" + str(ship_lost_id) + "_64.png")
            em.add_field(name="Victim",
                         value="Name: " + str(victim_name) + " \nCorp: " + str(victim_corp) + " \nAlliance: " + str(
                             victim_alliance) + " \n ")
            await client.send_message(channel_id, embed=em)
        else:
            continue


async def redis(client):
    zkill = "https://redisq.zkillboard.com/listen.php?queueID=" + client.user.id
    with urllib.request.urlopen(zkill) as url:
        return json.loads(url.read().decode())
