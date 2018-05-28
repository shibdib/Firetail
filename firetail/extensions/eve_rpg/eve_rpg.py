from discord.ext import commands
from firetail.lib import db
from firetail.core import checks
from firetail.utils import make_embed
import asyncio
import random


class EveRpg:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.config = bot.config
        self.logger = bot.logger
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.tick_loop())

    @commands.command(name='setRpg')
    async def _set_rpg(self, ctx):
        """Sets a channel as an RPG channel.
        Do **!setRpg** to have a channel relay all RPG events.
        The RPG includes players from all servers this instance of the bot is on."""
        sql = ''' REPLACE INTO eve_rpg_channels(server_id,channel_id,owner_id)
                  VALUES(?,?,?) '''
        author = ctx.message.author.id
        channel = ctx.message.channel.id
        server = ctx.message.guild.id
        values = (server, channel, author)
        await db.execute_sql(sql, values)
        self.logger.info('eve_rpg - {} added {} to the rpg channel list.')
        return await ctx.author.send('**Success** - Channel added.')

    @commands.command(name='rpg')
    @checks.spam_check()
    @checks.is_whitelist()
    async def _rpg(self, ctx):
        """Sign up for the RPG.
        If your server doesn't have an RPG channel have an admin do **!setRpg** to receive the game events.
        If you've already registered this will reset your account."""
        sql = ''' REPLACE INTO eve_rpg_players(server_id,player_id)
                  VALUES(?,?) '''
        author = ctx.message.author.id
        server = ctx.message.guild.id
        values = (server, author)
        await db.execute_sql(sql, values)
        self.logger.info('eve_rpg - ' + str(ctx.message.author) + ' added to the game.')
        return await ctx.author.send('**Success** - Welcome to the game.')

    @commands.command(name='rpgStats', aliases=["rpgstats"])
    @checks.spam_check()
    @checks.is_whitelist()
    async def _rpg_stats(self, ctx):
        """Get your RPG Stats"""
        sql = ''' SELECT * FROM eve_rpg_players WHERE `player_id` = (?) '''
        values = (ctx.message.author.id,)
        result = await db.select_var(sql, values)
        sql = ''' SELECT * FROM eve_rpg_players ORDER BY `level` DESC LIMIT 1 '''
        top_level = await db.select(sql)
        top_level_user = self.bot.get_user(int(top_level[0][2]))
        sql = ''' SELECT * FROM eve_rpg_players ORDER BY `kills` DESC LIMIT 1 '''
        top_killer = await db.select(sql)
        top_killer_user = self.bot.get_user(int(top_killer[0][2]))
        if result is None:
            return await ctx.author.send('**Error** - No player found.')
        else:
            ship_attack, ship_defense, ship_maneuverability, ship_tracking = await self.ship_attributes(result)
            item_attack, item_defense, item_maneuverability, item_tracking = await self.item_attributes(result)
            ship_stats = ' {}/{}/{}/{}'.format(ship_attack, ship_defense, ship_maneuverability, ship_tracking)
            item_stats = ' {}/{}/{}/{}'.format(item_attack, item_defense, item_maneuverability, item_tracking)
            embed = make_embed(guild=ctx.guild)
            embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                             text="Provided Via Firetail Bot")
            embed.add_field(name="Stats",
                            value='\n Level: {}\nXP: {}/100\nShip : {}\nAttack/Defense/Maneuverability/Tracking: {}\n'
                                  'Items: {}\nItem Bonuses (Already applied to ship): {}\nKills: {}\nLosses: {}'.format(
                                result[0][5], result[0][6], result[0][7], ship_stats, result[0][8], item_stats,
                                result[0][3], result[0][4]))
            embed.add_field(name="Top Players", value='\n Top Level: {} (Level {})\nMost Kills: {} ({} Kills)'.format(
                top_level_user.display_name, top_level[0][5], top_killer_user.display_name, top_killer[0][3]),
                            inline=False)
            await ctx.channel.send(embed=embed)

    @commands.command(name='rpgTop', aliases=["rpgtop"])
    @checks.spam_check()
    @checks.is_whitelist()
    async def _rpg_top(self, ctx):
        """Get the top RPG players"""
        sql = ''' SELECT * FROM eve_rpg_players WHERE `player_id` = (?) '''
        values = (ctx.message.author.id,)
        result = await db.select_var(sql, values)
        sql = ''' SELECT * FROM eve_rpg_players ORDER BY `level` DESC LIMIT 10 '''
        top_levels = await db.select(sql)
        top_levels_array = []
        for levels in top_levels:
            top_levels_user = self.bot.get_user(int(levels[2]))
            top_levels_array.append('{} - Level {}'.format(top_levels_user.display_name, levels[5]))
        levels_list = '\n'.join(top_levels_array)
        sql = ''' SELECT * FROM eve_rpg_players ORDER BY `kills` DESC LIMIT 10 '''
        top_killers = await db.select(sql)
        top_killers_array = []
        for killers in top_killers:
            top_killer_user = self.bot.get_user(int(killers[2]))
            top_killers_array.append('{} - {} Kills'.format(top_killer_user.display_name, killers[3]))
        killers_list = '\n'.join(top_killers_array)
        if result is None:
            return await ctx.author.send('**Error** - No player found. You must be part of the game to view this')
        else:
            embed = make_embed(guild=ctx.guild)
            embed.set_footer(icon_url=ctx.bot.user.avatar_url,
                             text="Provided Via Firetail Bot")
            embed.add_field(name="Level Leaderboard",
                            value=levels_list, inline=False)
            embed.add_field(name="Kills Leaderboard",
                            value=killers_list, inline=False)
            await ctx.channel.send(embed=embed)

    async def tick_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.process_turn()
                await asyncio.sleep(12)
            except Exception:
                self.logger.exception('ERROR:')
                await asyncio.sleep(5)

    async def process_turn(self):
        sql = ''' SELECT * FROM eve_rpg_players ORDER BY RANDOM() LIMIT 1 '''
        player = await db.select(sql)
        player_two = await db.select(sql)
        user = self.bot.get_user(int(player[0][2]))
        user_two = self.bot.get_user(int(player_two[0][2]))
        if user is None:
            self.logger.exception('eve_rpg - Bad player attempted removing....')
            return await self.remove_bad_user(player[0][2])
        if user_two is None:
            self.logger.exception('eve_rpg - Bad player attempted removing....')
            return await self.remove_bad_user(player_two[0][2])
        #  Get ship, set ibis if null
        ship = player[0][7]
        if ship is None:
            sql = ''' UPDATE eve_rpg_players
                    SET ship = (?)
                    WHERE
                        player_id = (?); '''
            values = ('Ibis', player[0][2],)
            await db.execute_sql(sql, values)
            ship = 'Ibis'
        ship_two = player_two[0][7]
        if ship_two is None:
            sql = ''' UPDATE eve_rpg_players
                    SET ship = (?)
                    WHERE
                        player_id = (?); '''
            values = ('Ibis', player_two[0][2],)
            await db.execute_sql(sql, values)
        #  Share turn
        #  PVP?
        pvp = await self.weighted_choice([(True, 13), (False, 45)])
        if user.id is user_two.id or pvp is False:
            ship_attack, ship_defense, ship_maneuverability, ship_tracking = await self.ship_attributes(player)
            #  PVE Rolls
            death = await self.weighted_choice(
                [(True, 11), (False, 75 + ((ship_defense * 1.5) + (ship_maneuverability * 1.2)))])
            flee = await self.weighted_choice(
                [(True, 13 + (ship_defense + (ship_maneuverability * 2))), (False, 80 - (ship_maneuverability * 2))])
            escalation = await self.weighted_choice([(True, 4), (False, 96)])
            if death is True and flee is False:
                message = await self.weighted_choice(
                    [('**{}** flying in a {} died to gate guns.'.format(user.display_name, ship), 10),
                     ('**{}** flying in a {} forgot to turn on their reps and died to rats.'.format(user.display_name,
                                                                                                    ship), 45),
                     ('**{}** flying in a {} went afk in an anomaly and died.'.format(user.display_name, ship), 45)])
                sql = ''' UPDATE eve_rpg_players
                        SET ship = (?)
                        WHERE
                            player_id = (?); '''
                values = ('Ibis', player[0][2],)
                await db.execute_sql(sql, values)
                await self.add_loss(player)
                return await self.send_turn(message)
            elif flee is True:
                message = await self.weighted_choice([(
                    '**{}** flying in a {} had to take a bio break mid anomaly and docked up.'.format(
                        user.display_name, ship), 10),
                    (
                        '**{}** flying in a {} overestimated their tank and fled the anomaly.'.format(
                            user.display_name, ship), 45),
                    (
                        '**{}** flying in a {} almost died to gankers but was aligned and got away.'.format(
                            user.display_name, ship), 45)])
                return await self.send_turn(message)
            else:
                if escalation is True:
                    message = await self.weighted_choice([(
                        '**{}** flying in a {} had their anomaly escalate and is enroute to the next system.'.format(
                            user.display_name, ship), 50),
                        ('**{}** flying in a {} got an escalation.'.format(
                            user.display_name, ship), 50)])
                    await self.send_turn(message)
                    death = await self.weighted_choice(
                        [(True, 11), (False, 75 + ((ship_defense * 1.5) + (ship_maneuverability * 1.2)))])
                    flee = await self.weighted_choice(
                        [(True, 13 + (ship_defense + (ship_maneuverability * 2))), (False, 87)])
                    if death is True and flee is False:
                        message = await self.weighted_choice([(
                            '**{}** flying in a {} died on their way to the escalation.'.format(
                                user.display_name, ship), 10),
                            (
                                '**{}** flying in a {} forgot to turn on their reps and died to escalation rats.'.format(
                                    user.display_name, ship), 45),
                            (
                                '**{}** flying in a {} ran into incursion rats on a gate and died.'.format(
                                    user.display_name, ship), 45),
                            ('**{}** flying in a {} shot a drifer, RIP.'.format(
                                user.display_name, ship), 45),
                            (
                                '**{}** flying in a {} went afk in the escalation and died.'.format(
                                    user.display_name, ship), 45)])
                        sql = ''' UPDATE eve_rpg_players
                                SET ship = (?),
                                    item = NULL
                                WHERE
                                    player_id = (?); '''
                        values = ('Ibis', player[0][2],)
                        await db.execute_sql(sql, values)
                        await self.add_loss(player)
                        return await self.send_turn(message)
                    elif flee is True:
                        message = await self.weighted_choice([(
                            '**{}** flying in a {} ran into a camp on the way and ran away.'.format(
                                user.display_name, ship), 10),
                            (
                                '**{}** flying in a {} overestimated their tank and fled the escalation.'.format(
                                    user.display_name, ship), 45),
                            (
                                '**{}** flying in a {} could not tank the escalation rats and had to flee.'.format(
                                    user.display_name, ship), 45),
                            (
                                '**{}** flying in a {} got camped into their home system and the escalation '
                                'expired.'.format(user.display_name, ship), 45),
                            (
                                '**{}** flying in a {} almost died to gankers but was aligned and got away.'.format(
                                    user.display_name, ship), 45)])
                        return await self.send_turn(message)
                xp_gained = await self.weighted_choice([(3, 45), (5, 15), (7, 5)])
                await self.add_xp(player, xp_gained)
                message = await self.weighted_choice(
                    [('**{}** flying in a {} completed an anomaly in PL staging.'.format(user.display_name, ship), 10),
                     ('**{}** flying in a {} successfully completed an anomaly.'.format(user.display_name, ship), 45),
                     ('**{}** flying in a {} ran a faction warfare node.'.format(user.display_name, ship), 45),
                     ('**{}** flying in a {} killed some belt rats.'.format(user.display_name, ship), 45),
                     ('**{}** flying in a {} killed some rats on a gate during a PVP op #iskPositive.'.format(
                         user.display_name, ship), 45),
                     ('**{}** flying in a {} AFK ratted their way thru an anomaly.'.format(user.display_name, ship),
                      45)])
                await self.send_turn(message)
                # Award ship
                weight = 14
                if ship == 'Ibis':
                    weight = 90
                ship_drop = await self.weighted_choice([(True, weight), (False, 76)])
                if ship_drop is True:
                    new_ship = await self.new_ship(player)
                    if new_ship is not None:
                        message = await self.weighted_choice([(
                            '**{}** swapped their {} for a **{}** that they found abandoned next to an old POS.'.format(
                                user.display_name, ship, new_ship), 10),
                            (
                                '**{}** wanted to fly something new so they traded in their {} for a **{}**.'.format(
                                    user.display_name, ship, new_ship), 45),
                            (
                                '**{}** sold some salvage and swapped their {} for a **{}**.'.format(
                                    user.display_name, ship, new_ship), 45)])
                        await self.send_turn(message)
                new_item = await self.new_item(player, escalation)
                if new_item is not None:
                    message = await self.weighted_choice(
                        [('**{}** salvaged a **{}**.'.format(user.display_name, new_item), 45),
                         ('**{}** sold the loot from their last fight and decided to buy a **{}**.'.format(
                             user.display_name, new_item), 45)])
                    await self.send_turn(message)
        else:
            #  PVP Rolls
            #  PVP Winner/Loser
            ship_attack, ship_defense, ship_maneuverability, ship_tracking = await self.ship_attributes(player)
            ship_attack_two, ship_defense_two, ship_maneuverability_two, ship_tracking_two = await self.ship_attributes(
                player_two)
            tracking_one = 1
            if ship_tracking < ship_maneuverability_two:
                tracking_one = 0.8
            tracking_two = 1
            if ship_tracking_two < ship_maneuverability:
                tracking_two = 0.8
            player_one_weight = (((player[0][5] + 1) * 0.5) + (ship_attack - (ship_defense_two / 2))) * tracking_one
            player_two_weight = (((player_two[0][5] + 1) * 0.5) + (ship_attack_two - (ship_defense / 2))) * tracking_two
            weight = '\n\n_Debug: Battle Weights (Higher is better) {} - {} | {} - {}_'.format(
                self.bot.get_user(int(player[0][2])).display_name, player_one_weight,
                self.bot.get_user(int(player_two[0][2])).display_name, player_two_weight)
            winner = await self.weighted_choice(
                [(player, ((player[0][5] + 1) + (ship_attack - (ship_defense_two / 2))) * tracking_one),
                 (player_two, ((player_two[0][5] + 1) + (ship_attack_two - (ship_defense / 2))) * tracking_two)])
            loser = player
            if winner is player:
                loser = player_two
            winner_name = self.bot.get_user(int(winner[0][2])).display_name
            loser_name = self.bot.get_user(int(loser[0][2])).display_name
            winner_ship = winner[0][7]
            loser_ship = loser[0][7]
            xp_gained = await self.weighted_choice([(5, 45), (7, 15), (10, 5)])
            message = await self.weighted_choice([(
                '**PVP** - **{}** flying in a {} got a dank tick when **{}** flying in a {} tried to gank him and '
                'failed.{}'.format(
                    winner_name, winner_ship, loser_name, loser_ship, weight), 10),
                (
                    '**PVP** - **{}** flying in a {} went AFK and got killed by **{}** in a {}.{}'.format(
                        loser_name, loser_ship, winner_name, winner_ship, weight), 45),
                (
                    '**PVP** - **{}** flying in a {} was trying to Krab but **{}** in a '
                    '{} had other ideas and killed him.{}'.format(
                        loser_name, loser_ship, winner_name, winner_ship, weight), 45),
                (
                    '**PVP** - **{}** flying in a {} ran into a **{}** while '
                    'roaming for content. Honorable PVP occurred and {} was '
                    'victorious.{}'.format(
                        loser_name, loser_ship, winner_ship, winner_name, weight), 10),
                (
                    '**PVP** - **{}** flying in a {} encountered **{}** on a gate '
                    'and was defeated by their superior {}.{}'.format(
                        loser_name, loser_ship, winner_name, winner_ship, weight), 45),
                (
                    '**PVP** - **{}** flying in a {} tried desperately to defeat '
                    '**{}** but was unable to escape the scram of the enemies {}.{}'.format(
                        loser_name, loser_ship, winner_name, winner_ship, weight), 45),
                (
                    '**PVP** - **{}** flying in a {} ran into **{}** in a {} on a gate and was killed as soon as he '
                    'de-cloaked.{}'.format(
                        loser_name, loser_ship, winner_name, winner_ship, weight), 10),
                (
                    '**PVP** - **{}** flying in a {} had their auto-pilot turned on and was killed by **{}** in a {} '
                    'at a gate.{}'.format(
                        loser_name, loser_ship, winner_name, winner_ship, weight), 45),
                (
                    '**PVP** - **{}** flying in a {} tried to warp away from a gate but **{}** in a {} was able to get '
                    'point and kill them.{}'.format(
                        loser_name, loser_ship, winner_name, winner_ship, weight), 45)
            ])
            await self.send_turn(message)
            sql = ''' UPDATE eve_rpg_players
                    SET ship = (?),
                        item = NULL
                    WHERE
                        player_id = (?); '''
            values = ('Ibis', loser[0][2],)
            await db.execute_sql(sql, values)
            await self.add_loss(loser)
            await self.add_kill(winner)
            await self.add_xp(winner, xp_gained)
            # Award ship
            weight = 14
            if winner_ship == 'Ibis':
                weight = 90
            ship_drop = await self.weighted_choice([(True, weight), (False, 76)])
            if ship_drop is True:
                new_ship = await self.new_ship(winner)
                if new_ship is not None:
                    message = await self.weighted_choice([(
                        '**{}** swapped their {} for a **{}** that they found abandoned next to an old POS.'.format(
                            winner_name, winner_ship, new_ship), 10),
                        (
                            '**{}** wanted to fly something new so they traded in their {} for a **{}**.'.format(
                                winner_name, winner_ship, new_ship), 45),
                        (
                            '**{}** sold the loot from their last fight and decided to swap their {} for a **{}**.'.format(
                                winner_name, winner_ship, new_ship), 45)])
                    await self.send_turn(message)
            new_item = await self.new_item(winner)
            if new_item is not None:
                message = await self.weighted_choice([('**{}** salvaged a **{}**.'.format(winner_name, new_item), 45),
                                                      ('**{}** sold the loot from their last fight and decided to '
                                                          'buy a **{}**.'.format(winner_name, new_item), 45),
                                                      ('**{}** found a **{}** in a wreck.'.format(
                                                          winner_name, new_item), 45)])
                await self.send_turn(message)

    async def send_turn(self, message):
        sql = "SELECT * FROM eve_rpg_channels"
        game_channels = await db.select(sql)
        for channels in game_channels:
            channel = self.bot.get_channel(int(channels[2]))
            if channel is None:
                self.logger.exception('eve_rpg - Bad Channel Attempted removing....')
                await self.remove_bad_channel(channels[2])
            await channel.send(message)

    async def remove_bad_user(self, player_id):
        sql = ''' DELETE FROM eve_rpg_players WHERE `player_id` = (?) '''
        values = (player_id,)
        await db.execute_sql(sql, values)
        return self.logger.info('eve_rpg - Bad player removed successfully')

    async def remove_bad_channel(self, channel_id):
        sql = ''' DELETE FROM eve_rpg_channels WHERE `channel_id` = (?) '''
        values = (channel_id,)
        await db.execute_sql(sql, values)
        return self.logger.info('eve_rpg - Bad Channel removed successfully')

    async def add_xp(self, player, xp_gained):
        if player[0][6] + xp_gained < 100:
            sql = ''' UPDATE eve_rpg_players
                    SET xp = (?)
                    WHERE
                        player_id = (?); '''
            values = (player[0][6] + xp_gained, player[0][2],)
        else:
            sql = ''' UPDATE eve_rpg_players
                    SET level = (?),
                        xp = (?)
                    WHERE
                        player_id = (?); '''
            values = (player[0][5] + 1, 0, player[0][2],)
        await db.execute_sql(sql, values)

    async def add_kill(self, player):
        sql = ''' UPDATE eve_rpg_players
                SET kills = (?)
                WHERE
                    player_id = (?); '''
        values = (int(player[0][3]) + 1, player[0][2],)
        await db.execute_sql(sql, values)

    async def add_loss(self, player):
        sql = ''' UPDATE eve_rpg_players
                SET losses = (?)
                WHERE
                    player_id = (?); '''
        values = (int(player[0][4]) + 1, player[0][2],)
        await db.execute_sql(sql, values)

    async def new_item(self, player, escalation=False):
        items = player[0][8]
        item = await self.weighted_choice(
            [('Armor Plate', 10), ('Shield Extender', 5), ('Gyrostabilizer', 8), ('MWD', 8), ('AB', 10), (None, 35)])
        if escalation is not False:
            item = await self.weighted_choice(
                [('Faction-Gyrostabilizer', 10), ('Faction-Shield Extender', 5), ('Deadspace-MWD', 8),
                 ('Deadspace-AB', 8), ('Officer-Shield Mod', 2), (None, 35)])
        if item is None:
            return None
        if items is not None and item in items:
            return None
        else:
            sql = ''' UPDATE eve_rpg_players
                    SET item = (?)
                    WHERE
                        player_id = (?); '''
            if items is not None:
                values = ('{}, {}'.format(items, item), player[0][2],)
            else:
                values = ('{}'.format(item), player[0][2],)
            await db.execute_sql(sql, values)
            return item

    async def new_ship(self, player):
        ship_tier = await self.weighted_choice([(1, 75), (2, 70), (3, 65), (4, 50 + player[0][5]),
                                                (5, 40 + player[0][5]), (6, 20 + player[0][5]), (7, player[0][5]),
                                                (8, -10 + player[0][5]), (9, -25 + player[0][5]), (10, -50 + player[0][5])])
        if ship_tier is 1:
            ship = await self.weighted_choice([('Rifter', 25), ('Slicer', 25), ('Firetail', 5), ('Dramiel', 5)])
        elif ship_tier is 2:
            ship = await self.weighted_choice([('Firetail', 15), ('Dramiel', 15), ('Thrasher', 15), ('Catalyst', 15),
                                               ('Claw', 10), ('Crusader', 10), ('Raptor', 10), ('Taranis', 10)])
        elif ship_tier is 3:
            ship = await self.weighted_choice([('Thrasher', 15), ('Svipul', 15), ('Jackdaw', 15), ('Coercer', 5)])
        elif ship_tier is 4:
            ship = await self.weighted_choice([('Caracal', 15), ('Vexor', 15), ('Moa', 15), ('Rupture', 15), ('Vexor Navy Issue', 5)])
        elif ship_tier is 5:
            ship = await self.weighted_choice([('Hurricane', 15), ('Ferox', 15), ('Drake', 15), ('Harbinger', 5),
                                               ('Vagabond', 5), ('Muninn', 5), ('Cerberus', 5), ('Eagle', 5)])
        elif ship_tier is 6:
            ship = await self.weighted_choice([('Tempest', 15), ('Raven', 15), ('Megathron', 15), ('Dominix', 15),
                                               ('Abaddon', 15), ('Vargur', 5), ('Paladin', 5), ('Panther', 5)])
        elif ship_tier is 7:
            ship = await self.weighted_choice([('Machariel', 15), ('Nightmare', 15), ('Rattlesnake', 15), ('Vindicator', 15),
                                               ('Barghest', 15), ('Thanatos', 3), ('Archon', 3), ('Nidhoggur', 3), ('Chimera', 3)])
        elif ship_tier is 8:
            ship = await self.weighted_choice([('Thanatos', 15), ('Archon', 15), ('Nidhoggur', 15), ('Naglfar', 15),
                                               ('Phoenix', 15), ('Nyx', 3), ('Hel', 3), ('Revenant', 1)])
        elif ship_tier is 9:
            ship = await self.weighted_choice([('Nyx', 15), ('Hel', 15), ('Wyvern', 15), ('Aeon', 15),
                                               ('Avatar', 3), ('Ragnarok', 3), ('Revenant', 1)])
        elif ship_tier is 10:
            ship = await self.weighted_choice([('Avatar', 15), ('Ragnarok', 15), ('Erebus', 15), ('Leviathan', 15),
                                               ('Revenant', 1)])
        else:
            ship = await self.weighted_choice([('Eagle', 15), ('Ferox', 15), ('Hurricane', 15), ('Drake', 5)])
        ship_attack, ship_defense, ship_maneuverability, ship_tracking = await self.ship_attributes(player)
        current_sum = ship_attack + ship_defense + ship_maneuverability + ship_tracking
        ship_attack, ship_defense, ship_maneuverability, ship_tracking = await self.ship_attributes(player, ship)
        new_sum = ship_attack + ship_defense + ship_maneuverability + ship_tracking
        if ship != player[0][7] and new_sum > current_sum:
            sql = ''' UPDATE eve_rpg_players
                    SET ship = (?)
                    WHERE
                        player_id = (?); '''
            values = (ship, player[0][2],)
            await db.execute_sql(sql, values)
            return ship
        else:
            return None

    async def ship_attributes(self, player, supplied_ship=None):
        ship = player[0][7]
        if supplied_ship is not None:
            ship = supplied_ship
        item_attack, item_defense, item_maneuverability, item_tracking = await self.item_attributes(player)
        if ship == 'Ibis':
            return 0 + item_attack, 0 + item_defense, 1 + item_maneuverability, 1 + item_tracking
        if ship == 'Rifter' or ship == 'Slicer':
            return 2 + item_attack, 1 + item_defense, 4 + item_maneuverability, 3 + item_tracking
        if ship == 'Dramiel' or ship == 'Firetail':
            return 3 + item_attack, 1 + item_defense, 5 + item_maneuverability, 3 + item_tracking
        if ship == 'Claw' or ship == 'Raptor' or ship == 'Crusader' or ship == 'Taranis':
            return 2 + item_attack, 1 + item_defense, 7 + item_maneuverability, 4 + item_tracking
        if ship == 'Catalyst' or ship == 'Thrasher' or ship == 'Coercer':
            return 6 + item_attack, 2 + item_defense, 3 + item_maneuverability, 4 + item_tracking
        if ship == 'Svipul' or ship == 'Jackdaw':
            return 5 + item_attack, 3 + item_defense, 3 + item_maneuverability, 4 + item_tracking
        if ship == 'Caracal':
            return 6 + item_attack, 3 + item_defense, 3 + item_maneuverability, 8 + item_tracking
        if ship == 'Rupture' or ship == 'Moa':
            return 9 + item_attack, 5 + item_defense, 2 + item_maneuverability, 2 + item_tracking
        if ship == 'Vexor':
            return 8 + item_attack, 5 + item_defense, 2 + item_maneuverability, 6 + item_tracking
        if ship == 'Vexor Navy Issue':
            return 12 + item_attack, 6 + item_defense, 2 + item_maneuverability, 6 + item_tracking
        if ship == 'Hurricane' or ship == 'Ferox' or ship == 'Harbinger':
            return 12 + item_attack, 6 + item_defense, 2 + item_maneuverability, 3 + item_tracking
        if ship == 'Vagabond':
            return 10 + item_attack, 5 + item_defense, 4 + item_maneuverability, 4 + item_tracking
        if ship == 'Muninn' or ship == 'Eagle':
            return 11 + item_attack, 5 + item_defense, 3 + item_maneuverability, 5 + item_tracking
        if ship == 'Cerberus':
            return 10 + item_attack, 4 + item_defense, 4 + item_maneuverability, 8 + item_tracking
        if ship == 'Drake':
            return 10 + item_attack, 8 + item_defense, 2 + item_maneuverability, 8 + item_tracking
        if ship == 'Tempest' or ship == 'Megathron' or ship == 'Abaddon':
            return 18 + item_attack, 10 + item_defense, 1 + item_maneuverability, 3 + item_tracking
        if ship == 'Raven':
            return 16 + item_attack, 10 + item_defense, 1 + item_maneuverability, 6 + item_tracking
        if ship == 'Dominix':
            return 14 + item_attack, 10 + item_defense, 1 + item_maneuverability, 6 + item_tracking
        if ship == 'Vargur' or ship == 'Paladin':
            return 18 + item_attack, 20 + item_defense, 1 + item_maneuverability, 3 + item_tracking
        if ship == 'Panther':
            return 16 + item_attack, 10 + item_defense, 6 + item_maneuverability, 3 + item_tracking
        if ship == 'Machariel' or ship == 'Nightmare' or ship == 'Vindicator':
            return 20 + item_attack, 15 + item_defense, 2 + item_maneuverability, 3 + item_tracking
        if ship == 'Barghest' or ship == 'Rattlesnake':
            return 20 + item_attack, 13 + item_defense, 3 + item_maneuverability, 5 + item_tracking
        if ship == 'Thanatos' or ship == 'Archon' or ship == 'Nidhoggur' or ship == 'Chimera':
            return 30 + item_attack, 45 + item_defense, 2 + item_maneuverability, 3 + item_tracking
        if ship == 'Naglfar' or ship == 'Phoenix':
            return 45 + item_attack, 40 + item_defense, 2 + item_maneuverability, 2 + item_tracking
        if ship == 'Nyx' or ship == 'Hel' or ship == 'Aeon' or ship == 'Wyvern':
            return 60 + item_attack, 65 + item_defense, 2 + item_maneuverability, 3 + item_tracking
        if ship == 'Ragnarok' or ship == 'Avatar' or ship == 'Erebus' or ship == 'Leviathan':
            return 80 + item_attack, 75 + item_defense, 1 + item_maneuverability, 1 + item_tracking
        if ship == 'Revenant':
            return 65 + item_attack, 70 + item_defense, 2 + item_maneuverability, 3 + item_tracking
        return 0 + item_attack, 0 + item_defense, 0 + item_maneuverability, 0 + item_tracking

    async def item_attributes(self, player):
        item_attack, item_defense, item_maneuverability, item_tracking = 0, 0, 0, 0
        items = player[0][8]
        if items is None:
            return 0, 0, 0, 0
        if 'Armor Plate' in items:
            item_defense = item_defense + 1
            item_maneuverability = item_maneuverability - 1
        if 'Shield Extender' in items:
            item_defense = item_defense + 1
        if 'Gyrostabilizer' in items:
            item_attack = item_attack + 1
            item_tracking = item_tracking + 1
        if 'MWD' in items:
            item_maneuverability = item_maneuverability + 2
            item_tracking = item_tracking - 1
        if 'AB' in items:
            item_maneuverability = item_maneuverability + 1
        if 'Officer-Shield Mod' in items:
            item_defense = item_defense + 4
        if 'Faction-Shield Extender' in items:
            item_defense = item_defense + 3
        if 'Faction-Gyrostabilizer' in items:
            item_attack = item_attack + 2
            item_tracking = item_tracking + 2
        if 'Deadspace-MWD' in items:
            item_maneuverability = item_maneuverability + 3
            item_tracking = item_tracking - 1
        if 'Deadspace-AB' in items:
            item_maneuverability = item_maneuverability + 2
        return item_attack, item_defense, item_maneuverability, item_tracking

    async def weighted_choice(self, items):
        """items is a list of tuples in the form (item, weight)"""
        weight_total = sum((item[1] for item in items))
        n = random.uniform(0, weight_total)
        for item, weight in items:
            if n < weight:
                return item
            n = n - weight
        return item
