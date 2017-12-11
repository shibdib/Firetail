from lib import esi
import urllib.request
import json
import discord


async def run(client, logger, config):
    #  Get latest kill data
    kill_data = await redis(client)
    #  Foreach thru all provided groups
    for group in config.killmail['killmailGroups']:
        killmail_group_id = config.killmail['killmailGroups'][group]['id']
        channel_id = config.killmail['killmailGroups'][group]['channelId']
        loss = config.killmail['killmailGroups'][group]['lossMails']
        #  Skip npc
        if kill_data['zkb']['npc'] == True or not kill_data['killmail']['victim']['corporation_id']:
            break
        #  Get all group id's from the mail
        group_ids = []
        if loss:
            group_ids.append(kill_data['killmail']['victim']['corporation_id'])
            if 'alliance_id' in kill_data['killmail']['victim']:
                group_ids.append(kill_data['killmail']['victim']['alliance_id'])
        for attacker in kill_data['killmail']['attackers']:
            if 'corporation_id' in attacker:
                group_ids.append(attacker['corporation_id'])
            if 'alliance_id' in attacker:
                group_ids.append(attacker['alliance_id'])
        if killmail_group_id in group_ids:
            kill_id = kill_data['killID']
            value_raw = kill_data['zkb']['totalValue']
            value = '{:,}'.format(float(value_raw))
            victim_id = kill_data['killmail']['victim']['character_id']
            victim_name = await esi.character_name(victim_id)
            ship_lost_id = kill_data['killmail']['victim']['ship_type_id']
            ship_lost_raw = await esi.type_info_search(ship_lost_id)
            ship_lost = ship_lost_raw['name']
            victim_corp_id = kill_data['killmail']['victim']['corporation_id']
            victim_corp_raw = await esi.corporation_info(victim_corp_id)
            victim_corp = victim_corp_raw['corporation_name']
            if 'alliance_id' in kill_data['killmail']['victim']:
                victim_alliance_id = kill_data['killmail']['victim']['alliance_id']
                victim_alliance_raw = await esi.alliance_info(victim_alliance_id)
                victim_alliance = victim_alliance_raw['alliance_name']
            solar_system_id = kill_data['killmail']['solar_system_id']
            solar_system_info = await esi.system_info(solar_system_id)
            solar_system_name = solar_system_info['name']
            title = victim_name + " Lost a " + ship_lost + " Valued At " + value + " ISK "
            em = discord.Embed(title=title.title(), description="Fight Occurred In: " + str(solar_system_name),
                               url="https://zkillboard.com/kill/" + str(kill_id) + "/", colour=0xDEADBF)
            em.set_footer(icon_url=client.user.default_avatar_url, text="Provided Via Firetail Bot + ZKill")
            em.set_thumbnail(url="https://image.eveonline.com/Type/" + str(ship_lost_id) + "_64.png")
            if 'alliance_id' in kill_data['killmail']['victim']:
                em.add_field(name="Victim",
                             value="Name: " + str(victim_name) + " \nCorp: " + str(victim_corp) + " \nAlliance: " + str(
                                 victim_alliance) + " \n ")
            else:
                em.add_field(name="Victim",
                             value="Name: " + str(victim_name) + " \nCorp: " + str(victim_corp))
            channel = client.get_channel(str(channel_id))
            logger.info('Killmail - Kill # ' + str(kill_id) + ' has been posted to ' + str(channel.name))
            await client.send_message(channel, embed=em)
        elif kill_data['zkb']['totalValue'] >= config.killmail['bigKillsValue'] and config.killmail['bigKills']:
            channel_id = config.killmail['bigKillsChannel']
            kill_id = kill_data['killID']
            value_raw = kill_data['zkb']['totalValue']
            value = '{:,}'.format(float(value_raw))
            victim_id = kill_data['killmail']['victim']['character_id']
            victim_name = await esi.character_name(victim_id)
            ship_lost_id = kill_data['killmail']['victim']['ship_type_id']
            ship_lost_raw = await esi.type_info_search(ship_lost_id)
            ship_lost = ship_lost_raw['name']
            victim_corp_id = kill_data['killmail']['victim']['corporation_id']
            victim_corp_raw = await esi.corporation_info(victim_corp_id)
            victim_corp = victim_corp_raw['corporation_name']
            if 'alliance_id' in kill_data['killmail']['victim']:
                victim_alliance_id = kill_data['killmail']['victim']['alliance_id']
                victim_alliance_raw = await esi.alliance_info(victim_alliance_id)
                victim_alliance = victim_alliance_raw['alliance_name']
            solar_system_id = kill_data['killmail']['solar_system_id']
            solar_system_info = await esi.system_info(solar_system_id)
            solar_system_name = solar_system_info['name']
            title = "**BIG KILL REPORTED:** " + victim_name + " Lost a " + ship_lost + " Valued At " + value + " ISK "
            em = discord.Embed(title=title.title(), description="Fight Occurred In: " + str(solar_system_name),
                               url="https://zkillboard.com/kill/" + str(kill_id) + "/", colour=0xDEADBF)
            em.set_footer(icon_url=client.user.default_avatar_url, text="Provided Via Firetail Bot + ZKill")
            em.set_thumbnail(url="https://image.eveonline.com/Type/" + str(ship_lost_id) + "_64.png")
            if 'alliance_id' in kill_data['killmail']['victim']:
                em.add_field(name="Victim",
                             value="Name: " + str(victim_name) + " \nCorp: " + str(victim_corp) + " \nAlliance: " + str(
                                 victim_alliance) + " \n ")
            else:
                em.add_field(name="Victim",
                             value="Name: " + str(victim_name) + " \nCorp: " + str(victim_corp))
            channel = client.get_channel(str(channel_id))
            logger.info('Killmail - Big Kill # ' + str(kill_id) + ' has been posted to ' + str(channel.name))
            await client.send_message(channel, embed=em)
        else:
            continue


async def redis(client):
    zkill = "https://redisq.zkillboard.com/listen.php?queueID=" + client.user.id
    with urllib.request.urlopen(zkill) as url:
        return json.loads(url.read().decode())['package']
