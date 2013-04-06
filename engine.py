import random
import copy
from collections import Counter as count


def generate_random_name():
    vocals = 'aaaeeeiiiooouuuyj'
    consonants = 'bcdfghklmnprstvwxz'
    vocals = [v for v in vocals]
    vocals += ['ue', 'ae', 'oe', 'au', 'qu']
    consonants = [c for c in consonants]
    name = ''
    while len(name) < random.randrange(3, 6):
        if len(name) == 0:
            if random.random() > 0.5:
                name += random.choice(vocals)
                if random.random() > 0.8:
                    num = 2
                else:
                    num = 1
                for i in range(num):
                    name += random.choice(consonants)
            else:
                name += random.choice(consonants)
        else:
            name += random.choice(vocals)
            if random.random() > 0.7:
                num = 2
            else:
                num = 1
            for i in range(num):
                name += random.choice(consonants)
    return name

class MapWarfare:

    def __init__(self, game_parameters):
        self.game_parameters = game_parameters
        self.players = {}
        self.sectors = {}
        self.ticks = 1
        self.num_players = 0

        # The id is used as a unique identifier of groups, buildings and
        self.current_id = {}

        for sector in self.game_parameters['engine_parameters']['all_sectors'].keys():
            self.sectors[sector] = False

    def new_player(self, nickname, hq_sector):
        # Check if nickname is not taken
        try:
            self.players[nickname]
            return False
        except KeyError:
            if nickname in ('others', 'all'):
                return False

        self.sectors[hq_sector] = nickname

        par = self.game_parameters
        self.num_players += 1

        self.players[
            nickname] = {'hq_sector': hq_sector, 'account': par['engine_parameters']['start_account'],
                         'groups': {}, 'transporter': {}, 'buildings': {}, 'cards': {}, 'victory_points': 0,
                         'player_num': self.num_players}

        self.current_id[nickname] = 0

        # Create home base (building #0), this is used by tests
        self.new_building(nickname, 0, hq_sector, 'Your Home Base', False)
        
        # Add extra units to start off...
        self.new_building(nickname, 1, hq_sector, 'Kaserne 1', False)
        self.new_group(nickname, [1], hq_sector, 'Ingeneur', False)
        self.new_group(nickname, [0, 0, 0, 0], hq_sector, 'Fighters', False)
        self.new_player('asshole', 10)
        
        title = 'Hi {0}!'.format(nickname)
        message = 'Welcome to the game! Why don\'t you buy some units, you have {0}$ in your account...'.format(
            self.players[nickname]['account'])
        msg_stack = {
            nickname: {'title': title, 'message': message, 'popup': True},
            'others': {'title': nickname + ' joined the game!', 'message': 'Be nice...', 'popup': False}}

        return msg_stack

    def get_victory_difference(self, nickname):
        # Calculate average without player
        all = []
        for name, player in self.players.items():
            if name != nickname:
                all.append(player['victory_points'])

        if all:
            avg = round(sum(all)/len(all),1)
        else:
            avg = 0
        return self.players[nickname]['victory_points'] - avg

    def get_id(self, player):
        pl = self.players[player]
        all_ids = pl['groups'].keys(
        ) + pl['transporter'].keys() + pl['buildings'].keys()
        if len(all_ids) > 0:
            for i in range(max(all_ids) + 2):
                if i not in all_ids:
                    break
        else:
            i = 0
        return i

    def new_group(self, nickname, units, sector, group_name='', costs=True):
        if costs:
            # All unit prices
            unit_prices = {}
            for unit_type, unit in self.game_parameters['unit_parameters'].items():
                unit_prices[unit_type] = int(unit['basic_parameters']['price'])

            # calculate total price for units
            total_price = 0
            for unit in units:
                total_price += unit_prices[unit]

            if total_price > self.players[nickname]['account']:
                return {nickname: {'title': 'Could not buy group', 'message': 'Probably not enough money...\n', 'popup': True}}
            else:
                self.players[nickname]['account'] -= total_price

        new_group_id = self.get_id(nickname)

        self.players[
            nickname]['groups'][new_group_id] = {'sector': sector, 'name': group_name,
                                                 'transporter': -1}
        unit_id = 0
        self.players[nickname]['groups'][new_group_id]['units'] = {}
        names = ''
        for unit in units:
            params = copy.deepcopy(self.game_parameters[
                                   'unit_parameters'][unit]['basic_parameters'])
            name = generate_random_name()
            names += name + ', '
            new_unit = {
                'name': name, 'parameters': params, 'age': 0, 'total_damage': 0,
                'protected': False, 'delay': 0, 'building': -1
            }

            self.players[nickname]['groups'][new_group_id][
                'units'][unit_id] = new_unit
            unit_id += 1

        try:
            price = total_price
        except UnboundLocalError:
            price = 0

        title = 'New Group: ID ' + str(new_group_id)
        message = 'You bought a new group, ID {0}, for {1}$.\n'.format(
            new_group_id, price)
        message += 'Say hi to: ' + names
        msg_stack = {nickname: {'title': title, 'message': message,
                                'popup': False}}
        return msg_stack

    def new_transporter(self, nickname, transporter_type, sector, transporter_name='', costs=True):

        params = copy.deepcopy(self.game_parameters['transport_parameters'][
                               transporter_type]['basic_parameters'])

        if costs:
            if params['price'] <= self.players[nickname]['account']:
                self.players[nickname]['account'] -= params['price']
            else:
                return {nickname: {'title': 'Could not buy transporter!', 'message': 'Probably not enough money...', 'popup': True}}

        new_id = self.get_id(nickname)

        new_transporter = {'sector': sector, 'name': transporter_name, 'parameters': params, 'current': [], 'age': 0,
                           'delay': 0, 'total_damage': 0, 'protected': False}

        self.players[nickname]['transporter'][new_id] = new_transporter

        title = 'New Transporter: ID ' + str(new_id)
        message = 'You bought a new transporter, ID {0}, for {1}$.\n'.format(
            new_id, params['price'])
        return {nickname: {'title': title, 'message': message, 'popup': False}}

    def new_building(self, nickname, building_type, sector, name='', costs=True):

        params = copy.deepcopy(self.game_parameters['building_parameters'][
                               building_type]['basic_parameters'])

        if costs:
            if params['price'] <= self.players[nickname]['account']:
                self.players[nickname]['account'] -= params['price']
            else:
                return {nickname: {'title': 'Could not buy building', 'message': 'Probably not enough money...', 'popup': True}}

        new_id = self.get_id(nickname)

        new_building = {'sector': sector, 'name': name, 'parameters': params, 'current': [], 'age': 0,
                        'delay': 0, 'total_damage': 0}
        self.players[nickname]['buildings'][new_id] = new_building

        title = 'New Building: ID ' + str(new_id)
        message = 'You bought a new building, ID {0}, for {1}$.'.format(
            new_id, params['price'])
        return {nickname: {'title': title, 'message': message, 'popup': False}}

    def rename_id(self, nickname, ind, name):
        pl = self.players[nickname]
        for id_type in ['groups', 'transporter', 'buildings']:
            if ind in pl[id_type].keys():
                self.players[nickname][id_type][ind]['name'] = name
                break

        return {}

    def new_card(self, nickname, amount):
        if self.players[nickname]['account'] >= amount:
            self.players[nickname]['account'] -= amount
            # Choose a random card from possible cards for this amount
            all_ind = []
            for card_ind in range(len(self.game_parameters['card_parameters'][amount])):
                card = self.game_parameters[
                    'card_parameters'][amount][card_ind]
                for i in range(card['num_cards']):
                    all_ind.append(card_ind)
            sel_card = random.choice(all_ind)
            card = self.game_parameters['card_parameters'][amount][sel_card]
            try:
                new_id = max(self.players[nickname]['cards'].keys()) + 1
            except ValueError:
                new_id = 0

            self.players[nickname]['cards'][new_id] = card

            title = 'New Card: ' + card['title']
            message = card['title'] + '\n\n' + card['description']
            msg_stack = {nickname: {'title': title, 'message':
                                    message, 'popup': True}}
        else:
            msg_stack = {nickname: {'title': 'Could not buy card', 'message':
                                    'Probably not enough money...', 'popup': True}}
        return msg_stack

    def perform_action(self, nickname, action, selection=False, o_id=False, u_id=False, sector=False):
        def make_changes(player, adress, changes):
            # decide which unit type is involved
            o_type = False
            if len(adress) == 2:
                # A Unit
                o_id, u_id = adress
                try:
                    u = self.players[player]['groups'][o_id]['units'][u_id]
                except KeyError:
                    return False
                o_type = 'groups'

            else:
                o_id = adress[0]
                if o_id in self.players[player]['transporter'].keys():
                    u = self.players[player]['transporter'][o_id]

                elif o_id in self.players[player]['buildings'].keys():
                    u = self.players[player]['buildings'][o_id]
                else:
                    return False

            # Make changes (always do max_life first)
            if 'max_life' in changes.keys():
                change = changes['max_life']

                new_change = round(random.normalvariate(
                    change, action['random'] * change), 0)
                if (u['parameters']['max_life'] + new_change) <= 0:
                    del u
                    if o_type == 'groups' and len(self.players[nickname]['groups'][o_id]['units']) == 0:
                        del self.players[nickname]['groups'][o_id]
                    return True
                else:
                    u['parameters']['max_life'] += new_change
                del changes['max_life']

            if 'life' in changes.keys():
                change = changes['life']

                new_change = round(random.normalvariate(
                    change, action['random'] * change), 0)
                if (u['parameters']['life'] + new_change) <= 0:
                    del u
                    if o_type == 'groups' and len(self.players[nickname]['groups'][o_id]['units']) == 0:
                        del self.players[nickname]['groups'][o_id]
                    return True
                else:
                    max_life = u['parameters']['max_life']
                    if u['parameters']['life'] + new_change > max_life:
                        new_change = max_life - u['parameters']['life']

                    u['parameters']['life'] += new_change

                del changes['life']

            for param, change in changes.items():
                if param in ('actions', 'shop_transporter', 'shop_units', 'name'):
                    new_change = change
                elif action['random'] > 0:
                    new_change = round(random.normalvariate(
                        change, action['random'] * change), 0)

                else:
                    new_change = round(change, 0)

                if param == 'actions':
                    for name, parameters in new_change.items():
                        u['parameters']['actions'][name] = parameters

                elif param == 'name':
                    u['name'] = new_change

                else:
                    try:
                        u['parameters'][param] += new_change
                    except KeyError, UnboundLocalError:
                        # E.g. if you try to change delay_walk of a building (does not have this parameter)
                        # or if the unit is already deleted
                        pass

            return True

        # Execute the action
        if action['type'] == 'new':
            if action['target'] in ('own', 'self'):
                player = nickname

            elif action['target'] == 'enemy':
                player = selection['enemy']

            # All new actions possible. These should all be free...
            if action['level'] == 'groups':
                self.new_group(
                    player, action['parameters'], sector, costs=False)
            elif action['level'] == 'transporter':
                self.new_transporter(
                    player, action['parameters'], sector, costs=False)
            elif action['level'] == 'buildings':
                self.new_building(
                    player, action['parameters'], sector, costs=False)
            return True

        elif action['type'] == 'change':
            if action['level'] == 'player':
                for param, change in action['changes'].items():
                    if param == 'name':
                        self.players[player]['name'] = change
                    else:
                        if action['random'] > 0:
                            new_change = round(random.normalvariate(
                                change, action['random'] * change), 0)
                        else:
                            new_change = round(change, 0)

                        self.players[player][param] += new_change
                return True

            elif action['target'] == 'self' and type(o_id) == int:
                if type(u_id) == int:
                    adress = (o_id, u_id)
                else:
                    adress = tuple([o_id])
                make_changes(nickname, adress, copy.deepcopy(action['changes']))
                return True

            elif action['target'] in ('own', 'enemy'):
                # Collect all the involved adresses
                if action['target'] == 'own':
                    pl = self.players[nickname]
                    player = nickname
                else:
                    player = selection['enemy']
                    pl = self.players[player]

                if action['num_units'] == 'all':
                    adresses = []
                    for g_id in pl['groups']:
                        for u_id in pl['groups'][g_id]['units']:
                            adresses.append((g_id, u_id))
                    for o_type in ['transporter', 'buildings']:
                        for o_id in pl[o_type].keys():
                            adresses.append(tuple([o_id]))
                else:
                    if action['target'] == 'own':
                        adresses = selection['own_selection']
                    else:
                        adresses = []
                        o_ids = selection['enemy_selection']
                        for o_id in o_ids:
                            if o_id in pl['groups'].keys():
                                for u_id in pl['groups'][o_id]['units'].keys():
                                    adresses.append((o_id, u_id))
                            else:
                                adresses.append(tuple([o_id]))

                    # If too many units: remove random units
                    while 0 < len(adresses) > action['num_units'] and not action['num_units'] == 'all':
                        ind = random.randrange(len(adresses))
                        adresses.pop(ind)

                    # If not enough duplicate random units
                    orig_adresses = adresses[:]
                    while 0 < len(adresses) < action['num_units'] and not action['num_units'] == 'all':
                        ind = random.randrange(len(orig_adresses))
                        adresses.append(orig_adresses[ind])

                # Perform all the changes
                for adress in adresses:
                    make_changes(player, adress, copy.deepcopy(action['changes']))
                return True

        return False

    def play_card(self, nickname, c_id, selection=False, sector=False):
        card = self.players[nickname]['cards'][c_id]
        # perform all actions on card
        for action in card['actions']:
            if not sector:
                sector = self.players[nickname]['hq_sector']

            success = self.perform_action(
                nickname, action, selection, sector=sector)

        msg = {'title': 'Card: ' + card['title'], 'message':
               'You played: {0}\n{1}'.format(card['title'], card['description']), 'popup': True}
        msg_others = {'title': '{0} played: {1}'.format(nickname, card['title']),
                      'message': '{0}\n{1}'.format(card['title'], card['description']),
                      'popup': False}

        del self.players[nickname]['cards'][c_id]

        return {nickname: msg, 'others': msg_others}

    def perform_unit_action(self, nickname, action_name, o_id, u_id=False, selection=False, sector=False):
        '''Performs a specified unit action, returns a msg_stack or empty message  stack {}'''
        to_del = False
        # Also withraw one from the use counter, if there are no uses left:
        # delete action
        if type(u_id) == int:
            try:
                obj_act = self.players[nickname]['groups'][
                    o_id]['units'][u_id]['parameters']['actions']
            except KeyError:
                return {nickname: {'title': 'Seems to be dead unit:' + str(o_id) + ', ' + str(u_id), 'message': 'No action', 'popup': False}}

            cat = obj_act[action_name]['category']
            if cat != 'upgrade' and self.players[nickname]['groups'][o_id]['units'][u_id]['delay'] > 0:
                return {nickname: {'title': 'You are delayed...', 'message': 'No action', 'popup': False}}
        else:
            try:
                obj_act = self.players[nickname][
                    'transporter'][o_id]['parameters']['actions']
                cat = obj_act[action_name]['category']
                if cat != 'upgrade' and self.players[nickname]['transporter'][o_id]['delay'] > 0:
                    return {nickname: {'title': 'You are delayed...', 'message': 'No action', 'popup': False}}

            except KeyError:
                obj_act = self.players[nickname][
                    'buildings'][o_id]['parameters']['actions']
                cat = obj_act[action_name]['category']
                if cat != 'upgrade' and self.players[nickname]['buildings'][o_id]['delay'] > 0:
                    return {nickname: {'title': 'You are delayed...', 'message': 'No action', 'popup': False}}

        action = obj_act[action_name]
        if action['num_uses'] > 1:
            obj_act[action_name]['num_uses'] -= 1
        elif action['num_uses'] == -1:
            pass
        else:
            to_del = True

        if action['price'] <= self.players[nickname]['account']:
            self.players[nickname]['account'] -= action['price']

            # Perform all actions and return message stack
            success = True
            for act in action['actions']:
                su = self.perform_action(
                    nickname, act, selection, o_id, u_id, sector)
                if not su:
                    success = False

            # apply delay in any case
            delay = action['delay']

            if type(u_id) == int:
                self.players[nickname]['groups'][o_id][
                    'units'][u_id]['delay'] += delay

            else:
                try:
                    self.players[nickname][
                        'transporter'][o_id]['delay'] += delay
                except KeyError:
                    try:
                        self.players[nickname][
                            'buildings'][o_id]['delay'] += delay
                    except KeyError:
                        pass

            if to_del:
                del obj_act[action_name]

            if success:
                msg_stack = {nickname: {'title': 'Performed Unit Action', 'message': str(action),
                                        'popup': False}}

            else:
                msg_stack = {nickname: {'title': 'Could Not Perform All requested Actions', 'message': str(action),
                                        'popup': True}}
        else:
            msg_stack = {nickname: {'title': 'Not enough $$ for Action', 'message': str(action),
                                    'popup': True}}

        return msg_stack

    def move_units(self, nickname, changes, new_name=''):
        '''Moves units between groups'''
        new_group_id = -1
        sector = False

        for unit_coord, new_group in changes.items():
            g_id, u_id = unit_coord
            unit = self.players[nickname]['groups'][g_id]['units'][u_id]

            if type(sector) != int:
                sector = self.players[nickname]['groups'][g_id]['sector']

            if new_group != -1:
                keys = self.players[nickname]['groups'][
                    new_group]['units'].keys()
                if keys:
                    new_id = max(keys) + 1
                else:
                    new_id = 0

                self.players[nickname]['groups'][
                    new_group]['units'][new_id] = unit

            else:
                if new_group_id == -1:
                    new_group_id = self.get_id(nickname)
                    # Create a new group with no units
                    self.new_group(nickname, [], sector, new_name, False)

                keys = self.players[nickname]['groups'][
                    new_group_id]['units'].keys()
                if keys:
                    new_id = max(keys) + 1
                else:
                    new_id = 0

                self.players[nickname]['groups'][
                    new_group_id]['units'][new_id] = unit

            del self.players[nickname]['groups'][g_id]['units'][u_id]
            if len(self.players[nickname]['groups'][g_id]['units']) == 0:
                del self.players[nickname]['groups'][g_id]

        message = 'You moved units.'
        msg_stack = {nickname: {'title': 'Moved Units', 'message':
                                message, 'popup': False}}
        return msg_stack

    def get_all_enemy_groups(self, nickname):
        '''returns enemy groups and which sector they are placed in'''

        enemy_groups = {}
        for player in self.players.keys():
            if player != nickname:
                all_groups = {}
                pl = self.players[player]
                types = ['groups', 'transporter', 'buildings']
                for t in types:
                    for o_id, obj in pl[t].items():
                        all_groups[o_id] = obj['sector']

                if all_groups:
                    enemy_groups[player] = all_groups

        return enemy_groups

    def protect_groups(self, nickname, groups):
        '''only soldiers can be protected...'''
        num_protected = 0
        for g_id in groups:
            for u_id, unit in self.players[nickname]['groups'][g_id]['units'].items():
                # only soldiers can be protected
                if unit['parameters']['unit_type'] == 'soldier':
                    if (not unit['protected']) and (unit['delay'] == 0):
                        disabled = self.game_parameters[
                            'engine_parameters']['protection_in']
                        self.players[nickname][
                            'groups'][g_id]['units'][u_id]['delay'] = disabled
                        self.players[nickname][
                            'groups'][g_id]['units'][u_id]['protected'] = True

                        num_protected += 1

        if num_protected > 0:
            title = 'Protected Groups'
            message = 'You protected all units in the following groups:\n{0}.'.format(
                groups)
            msg = {nickname: {'title': title, 'message':
                              message, 'popup': False}}
        else:
            msg = {nickname: {'title': 'Could not protect any units in the groups.', 'message':
                              'The title says it all...', 'popup': False}}

        return msg

    def unprotect_groups(self, nickname, groups):
        num_protected = 0
        for g_id in groups:
            for u_id, unit in self.players[nickname]['groups'][g_id]['units'].items():
                # only soldiers can be protected
                if unit['parameters']['unit_type'] == 'soldier':
                    if unit['protected'] and (unit['delay'] == 0):
                        disabled = self.game_parameters[
                            'engine_parameters']['protection_out']
                        self.players[nickname]['groups'][
                            g_id]['units'][u_id]['protected'] = False
                        self.players[nickname][
                            'groups'][g_id]['units'][u_id]['delay'] = disabled
                        num_protected += 1

        if num_protected > 0:
            title = 'Protected Groups'
            message = 'You moved all units in the following groups out of protection:\n{0}.'.format(
                groups)
            msg = {nickname: {'title': title, 'message':
                              message, 'popup': False}}
        else:
            msg = {nickname: {'title': 'Could not unprotect any units in the groups.', 'message':
                              'The title says it all...', 'popup': False}}

        return msg

    def enter_building(self, nickname, g_id, b_id):
        group = self.players[nickname]['groups'][g_id]
        build = self.players[nickname]['buildings'][b_id]

        # Check if group hasnt made action yet
            # Check if group is not being transported or protected
        if group['transporter'] == -1:
            # Check if building has any capacity for units left
            capacity = build['parameters']['capacity'] - len(build['current'])
            # make a list of all units that want to enter
                #&Check if any unit is in another building
            accepts = build['parameters']['enter']
            other_building = False
            unit_requests = []
            for u_id, unit in group['units'].items():
                if unit['building'] not in (b_id, -1) and (not unit['protected']):
                    other_building = True
                    break
                elif unit['building'] == -1:
                    # check if unit can enter the building
                    if unit['parameters']['unit_type'] == accepts and unit['delay'] == 0:
                        unit_requests.append(u_id)

            while len(unit_requests) > capacity:
                ind = random.randrange(len(unit_requests))
                unit_requests.pop(ind)

            if (not other_building) and unit_requests:
                # Load units in building until capacity met or no units left
                    # Apply delay and made action only to units
                disable = build['parameters']['delay_in']
                for unit in unit_requests:
                    self.players[nickname][
                        'buildings'][b_id]['current'].append((g_id, unit))
                    self.players[nickname]['groups'][
                        g_id]['units'][unit]['building'] = b_id
                    self.players[nickname]['groups'][
                        g_id]['units'][unit]['delay'] = disable

                title = 'Units from group {0} entered building {1}'.format(
                    g_id, b_id)
                message = ''
                return {nickname: {'title': title, 'message': message, 'popup': False}}

        return {nickname: {'title': 'Could Not Enter Building', 'message': 'The title says it all...', 'popup': True}}

    def exit_building(self, nickname, g_id):
        group = self.players[nickname]['groups'][g_id]

        # Make a list of all the units that can exit
        b_id = -1
        all_units = []
        for u_id, unit in group['units'].items():
            if unit['building'] != -1:
                b_id = unit['building']
                if unit['delay'] == 0:
                    all_units.append(u_id)

        if b_id != -1 and all_units:
            build = self.players[nickname]['buildings'][b_id]
            delay = build['parameters']['delay_out']

            for u_id, unit in group['units'].items():
                if self.players[nickname]['groups'][g_id]['units'][u_id]['building'] == b_id:
                    self.players[nickname][
                        'buildings'][b_id]['current'].remove((g_id, u_id))
                    self.players[nickname]['groups'][
                        g_id]['units'][u_id]['building'] = -1
                    self.players[nickname]['groups'][
                        g_id]['units'][u_id]['delay'] = delay

            title = 'Units in group {0} exited building {1}'.format(g_id, b_id)
            message = ''
            return {nickname: {'title': title, 'message': message, 'popup': False}}

        return {nickname: {'title': 'Could Not Unload', 'message': 'The title says it all...', 'popup': False}}

    def load_transporter(self, nickname, g_id, t_id):
        group = self.players[nickname]['groups'][g_id]
        trans = self.players[nickname]['transporter'][t_id]

        # Check if transporter has enough capacity
        num_units = len(group['units'].keys())
        num_in_transporter = 0
        for group in trans['current']:
            num_in_transporter += len(
                self.players[nickname]['groups'][group]['units'])

        if num_units <= trans['parameters']['capacity'] - num_in_transporter:
            # Check if all units in group can be transported with transporter
            found = False
            for u_id, unit in group['units'].items():
                if unit['parameters']['unit_type'] != trans['parameters']['transports']:
                    found = True
                    break

            # Toggle transport for all units units and transporter will be disabled during this time
                # if unit is transported it will not be able to move and defend
                # itself
            if not found:
                self.players[nickname]['transporter'][
                    t_id]['delay'] = trans['parameters']['delay_in']
                self.players[nickname]['transporter'][
                    t_id]['current'].append(g_id)

                for u_id in group['units'].keys():
                    self.players[nickname]['groups'][g_id][
                        'units'][u_id]['delay'] = trans['parameters']['delay_in']

                self.players[nickname]['groups'][g_id]['transporter'] = t_id

                title = 'Loaded {0} in transporter {1}'.format(g_id, t_id)
                message = ''
                return {nickname: {'title': title, 'message': message, 'popup': False}}

        return {nickname: {'title': 'Could Not Transport', 'message': 'The title says it all...', 'popup': False}}

    def unload_group(self, nickname, g_id):
        group = self.players[nickname]['groups'][g_id]
        # check if group is being transported
        t_id = group['transporter']
        if t_id != -1:
            trans = self.players[nickname]['transporter'][t_id]
            disable = trans['parameters']['delay_out']
            self.players[nickname]['transporter'][t_id]['delay'] = disable

            self.players[nickname]['transporter'][t_id]['current'].remove(g_id)
            self.players[nickname]['groups'][g_id]['transporter'] = -1

            for u_id in group['units'].keys():
                self.players[nickname]['groups'][g_id][
                    'units'][u_id]['delay'] = disable

            title = 'Unloaded {0} from transporter {1}'.format(g_id, t_id)
            message = ''
            return {nickname: {'title': title, 'message': message, 'popup': False}}

        return {nickname: {'title': 'Could Not Unload', 'message': 'The title says it all...', 'popup': False}}

    def move_into_sector(self, nickname, o_id, sector):
        '''move an id (group or transporter) into a sector'''
        pl = self.players[nickname]
        # Check if object is a transporter
        #& set all involved groups (&transporter) to new sector
        moved = False
        if o_id in pl['transporter'].keys():
            if pl['transporter'][o_id]['delay'] == 0:
                moved = True
                self.players[nickname]['transporter'][o_id]['sector'] = sector
                current = pl['transporter'][o_id]['current']
                if current != []:
                    for g_id in current:
                        self.players[nickname][
                            'groups'][g_id]['sector'] = sector

                # set delay
                delay = self.players[nickname][
                    'transporter'][o_id]['parameters']['delay_walk']
                self.players[nickname]['transporter'][o_id]['delay'] = delay

        else:
            found = False
            for unit in pl['groups'][o_id]['units'].values():
                if unit['delay'] > 0:
                    found = True
                    break

            if not found:
                moved = True
                pl['groups'][o_id]['sector'] = sector
                g = self.players[nickname]['groups'][o_id]
                # apply walk delay to all units
                for u_id, unit in g['units'].items():
                    self.players[nickname]['groups'][o_id]['units'][
                        u_id]['delay'] = unit['parameters']['delay_walk']

        # if moved check:
        # if player has now more than "take_over_factor" times life in the
        # sector
        if moved:
            current = self.sectors[sector]
            if current and current != nickname:
                # how much life does player and current owner have in sector
                total_life = {}
                for player in (nickname, current):
                    total_life[player] = 0
                    pl = self.players[player]
                    for group in pl['groups'].values():
                        if group['sector'] == sector:
                            for unit in group['units'].values():
                                total_life[
                                    player] += unit['parameters']['life']
                    for o_type in ('transporter', 'buildings'):
                        for obj in pl[o_type].values():
                            if obj['sector'] == sector:
                                total_life[player] += obj['parameters']['life']

                eng_par = self.game_parameters['engine_parameters']

                # takeover factor scales life required
                required = total_life[current] * eng_par['take_over_factor']

                if required <= total_life[nickname]:
                    # Give take over reward scaled to value of sector
                    reward = round(eng_par['sector_takeover']
                                   * eng_par['all_sectors'][sector]['weight'], 0)
                    self.players[nickname]['account'] += reward
                    # current possessor ==> take over the sector from player
                    self.sectors[sector] = nickname

            elif not current:
                self.sectors[sector] = nickname

    def on_tick(self):
        '''This function performs all the updates initiated by a tick.'''
        # give constant money
        # give money for sectors
        for nickname in self.players.keys():
            eng_par = self.game_parameters['engine_parameters']

            # add constant reward for sector possession
            self.players[nickname]['account'] += eng_par['constant_per_tick']

            own_sectors = [sec for sec,
                           player in self.sectors.items() if player == nickname]
            for sec in own_sectors:
                # Reward scaled to sector importance
                reward = round(eng_par['per_sector_per_tick'] *
                               eng_par['all_sectors'][sec]['weight'], 0)
                self.players[nickname]['account'] += reward

                # Give victory points
                self.players[nickname]['victory_points'] += eng_par['all_sectors'][sec]['victory']

            for g_id, group in self.players[nickname]['groups'].items():
                # Set all groups action_made
                for u_id, unit in group['units'].items():
                    # subtract 1 round from all units which are disabled
                    if unit['delay'] > 0:
                        self.players[nickname][
                            'groups'][g_id]['units'][u_id]['delay'] -= 1
                    # add one age
                    self.players[nickname]['groups'][
                        g_id]['units'][u_id]['age'] += 1

            for t_id, trans in self.players[nickname]['transporter'].items():
                # Set all groups action_made & add age
                self.players[nickname]['transporter'][t_id]['age'] += 1
                if trans['delay'] > 0:
                    self.players[nickname]['transporter'][t_id]['delay'] -= 1

            for b_id, building in self.players[nickname]['buildings'].items():
                # Set all groups action_made & add age
                self.players[nickname]['buildings'][b_id]['age'] += 1
                if building['delay'] > 0:
                    self.players[nickname]['buildings'][b_id]['delay'] -= 1

            # Check if any unit upgrades to elite status
            # because of total_damage
            # create a map of all upgrade_levels
            upgrades = {}
            upgrades['groups'] = {}
            for u_id, unit in self.game_parameters['unit_parameters'].items():
                upgrades['groups'][u_id] = unit['elite_parameters']['ticks']

            upgrades['transporter'] = {}
            for t_id, trans in self.game_parameters['transport_parameters'].items():
                upgrades['transporter'][t_id] = trans[
                    'elite_parameters']['ticks']

            upgrades['buildings'] = {}
            for b_id, buil in self.game_parameters['building_parameters'].items():
                upgrades['buildings'][b_id] = buil['elite_parameters']['ticks']

            for g_id, group in self.players[nickname]['groups'].items():
                for u_id, unit in group['units'].items():
                    for border, actions in upgrades['groups'][unit['parameters']['id']].items():
                        if unit['age'] == border:
                            # perform the upgrades
                            for action in actions:
                                self.perform_action(nickname, action,
                                                    o_id=g_id, u_id=u_id, sector=group['sector'])

            for o_type in ('transporter', 'buildings'):
                for o_id, obj in self.players[nickname][o_type].items():
                    for border, actions in upgrades[o_type][obj['parameters']['id']].items():
                        if obj['age'] == border:
                            # perform the upgrades
                            for action in actions:
                                self.perform_action(nickname,
                                                    action, o_id=o_id, sector=obj['sector'])

            # Remove all groups with no units left
            for g_id, group in self.players[nickname]['groups'].items():
                if len(group['units'].keys()) == 0:
                    del self.players[nickname]['groups'][g_id]

        self.ticks += 1

        return {'all': {'title': 'Tick Tock', 'message': 'A new tick has passed...', 'popup': False}}

    def fight(self, starters, enemies, distance):

        def create_agent(obj):
            # How many shots how much damage per shot
            o_p = obj['parameters']
            ext_shoot_dist = self.game_parameters['engine_parameters']['extra_shoot_dist']
            num_shots = o_p['num_enemies']

            if o_p['attack_max'] > 0:
                attack = random.randrange(o_p['attack_min'] * 1000, o_p['attack_max'] * 1000) / float(1000)
            else:
                attack = 0
                num_shots = 0

            if o_p['shoot_dist'] >= distance:

                if obj['delay'] <= 0:
                    delay = True
                else:
                    damage_factor = self.game_parameters['engine_parameters']['delay_damage']
                    attack *= damage_factor
                    delay = False

            elif distance <= o_p['shoot_dist'] + ext_shoot_dist:
                # scale attack by extra shoot dist
                attack *= (float(distance) - o_p['shoot_dist'])/ext_shoot_dist
                if obj['delay'] <= 0:
                    delay = True
                else:
                    damage_factor = self.game_parameters['engine_parameters']['delay_damage']
                    attack *= damage_factor
                    delay = False

            else:
                attack = 0
                num_shots = 0
                delay = False

            if attack > 0 and num_shots > 0:
                attack = round(attack/num_shots, 0)

            return {'attack': attack, 'num_shots': num_shots, 'shield_factor': o_p['shield_factor'], 'delay': delay}

        def aggregate_agents(players, team):
            agents = {}
            for player, o_ids in players.items():
                pl = self.players[player]
                for o_id in o_ids:
                    if o_id in pl['groups'].keys():
                        group = pl['groups'][o_id]
                        for u_id, unit in group['units'].items():
                            # The unit adress
                            adress = (team, player, 'groups', (o_id, u_id))
                            if group['transporter'] == -1:
                                agents[adress] = create_agent(unit)
                            else:
                                agents[adress] = {
                                    'attack': 0, 'num_shots': 0, 'shield_factor': 0}

                    elif o_id in pl['transporter'].keys():
                        adress = (team, player, 'transporter', o_id)
                        agents[adress] = create_agent(pl['transporter'][o_id])

                    elif o_id in pl['buildings'].keys():
                        adress = (team, player, 'buildings', o_id)
                        agents[adress] = create_agent(pl['buildings'][o_id])

            return agents

        all_agents = aggregate_agents(starters, 'starters')
        all_agents.update(aggregate_agents(enemies, 'enemies'))

        apply_delay = []
        dead = {}

        total_damage = {'starters': 0, 'enemies': 0}
        # execute shots in random order
        shots_left = True
        while shots_left:
            # pick a random agent
            selected_adress = random.choice(all_agents.keys())
            selected_agent = all_agents[selected_adress]

            team = selected_adress[0]

            if selected_agent['num_shots'] > 0:
                selected_agent['num_shots'] -= 1
                executed = False
                # pick random agents until an enemy is found
                for i in range(25):
                    ad = random.choice(all_agents.keys())
                    if ad[0] != team:
                        executed = True
                        # deal damage to unit in group
                        if ad[2] == 'groups':
                            g_id, u_id = ad[3]
                            obj = self.players[
                                ad[1]]['groups'][g_id]['units'][u_id]
                            o_p = obj['parameters']

                            attack = selected_agent['attack']
                            # units can be damaged less if protected or in
                            # building
                            if obj['protected'] or (obj['building'] != -1):
                                attack = attack * (1 - (random.random() *
                                                        self.game_parameters['engine_parameters']['protection_effect']))

                            if o_p['shield'] > 0:
                                attack *= selected_agent['shield_factor']
                                attack = int(round(attack, 0))

                                if o_p['shield'] - attack > 0:
                                    self.players[ad[1]]['groups'][
                                        g_id]['units'][u_id]['parameters']['shield'] -= attack
                                else:
                                    self.players[ad[1]][
                                        'groups'][g_id]['units'][u_id]['parameters']['shield'] = 0
                            else:
                                attack = int(round(attack, 0))
                                if o_p['life'] - attack > 0:
                                    self.players[ad[1]][
                                        'groups'][g_id]['units'][u_id]['parameters']['life'] -= attack
                                else:
                                    # Delete the unit
                                    try:
                                        dead[ad[1]].append(self.players[
                                            ad[1]]['groups'][g_id]['units'][u_id]['parameters']['name'])
                                    except KeyError:
                                        dead[ad[1]] = [self.players[
                                            ad[1]]['groups'][g_id]['units'][u_id]['parameters']['name']]

                                    del self.players[
                                        ad[1]]['groups'][g_id]['units'][u_id]
                                    # delete the agent
                                    del all_agents[ad]
                                    # Check if the group is empty now and
                                    # delete
                                    if len(self.players[ad[1]]['groups'][g_id]['units']) == 0:
                                        del self.players[ad[1]]['groups'][g_id]

                                    if ad in apply_delay:
                                        apply_delay.remove(ad)

                        # deal damage to transporter / building
                        else:
                            obj = self.players[ad[1]][ad[2]][ad[3]]
                            o_p = obj['parameters']

                            attack = selected_agent['attack']

                            if o_p['shield'] > 0:
                                attack *= selected_agent['shield_factor']
                                attack = int(round(attack, 0))
                                if o_p['shield'] - attack > 0:
                                    self.players[ad[1]
                                                 ][ad[2]][ad[3]]['parameters']['shield'] -= attack
                                else:
                                    self.players[
                                        ad[1]][ad[2]][ad[3]]['parameters']['shield'] = 0
                            else:
                                attack = int(round(attack, 0))
                                if o_p['life'] - attack > 0:
                                    self.players[ad[
                                        1]][ad[2]][ad[3]]['parameters']['life'] -= attack
                                else:
                                    try:
                                        dead[ad[1]].append(self.players[ad[1]][ad[2]][ad[3]]['parameters']['name'])
                                    except KeyError:
                                        dead[ad[1]] = [self.players[ad[1]][ad[2]][ad[3]]['parameters']['name']]

                                    # Delete the object
                                    del self.players[ad[1]][ad[2]][ad[3]]
                                    # delete the agent
                                    del all_agents[ad]

                                    if ad in apply_delay:
                                        apply_delay.remove(ad)

                        if selected_adress not in apply_delay and selected_agent['delay']:
                            apply_delay.append(selected_adress)
                        break

                if executed:
                    if selected_adress[2] == 'groups':
                        ad = selected_adress
                        g_id, u_id = ad[3]
                        obj = self.players[ad[1]][
                            'groups'][g_id]['units'][u_id]

                        damage_before = obj['total_damage']
                        self.players[ad[1]]['groups'][
                            g_id]['units'][u_id]['total_damage'] += attack
                        damage_after = self.players[ad[1]][
                            'groups'][g_id]['units'][u_id]['total_damage']

                        total_damage[ad[0]] += damage_after - damage_before

                        unit_type_id = obj['parameters']['id']
                        upgrades = self.game_parameters[
                            'unit_parameters'][unit_type_id]['elite_parameters']['damage']

                        for border, actions in upgrades.items():
                            if damage_before < border < damage_after:
                                # perform the upgrade
                                sector = self.players[
                                    ad[1]]['groups'][g_id]['sector']
                                for action in actions:
                                    self.perform_action(ad[1], action, g_id,
                                                        u_id, sector=sector)

                    else:
                        ad = selected_adress
                        obj = self.players[ad[1]][ad[2]][ad[3]]

                        damage_before = obj['total_damage']
                        self.players[ad[1]][ad[2]][
                            ad[3]]['total_damage'] += attack
                        damage_after = self.players[
                            ad[1]][ad[2]][ad[3]]['total_damage']

                        total_damage[ad[0]] += damage_after - damage_before

                        unit_type_id = obj['parameters']['id']
                        if ad[2] == 'buildings':
                            params = 'building_parameters'
                        elif ad[2] == 'transporter':
                            params = 'transport_parameters'

                        upgrades = self.game_parameters[
                            params][unit_type_id]['elite_parameters']['damage']

                        for border, actions in upgrades.items():
                            if damage_before < border < damage_after:
                                # perform the upgrade
                                sector = self.players[
                                    ad[1]][ad[2]][ad[3]]['sector']
                                for action in actions:
                                    self.perform_action(
                                        ad[1], action, ad[3], u_id=False, sector=sector)

            shots_left = False
            for agent in all_agents.values():
                if agent['num_shots'] > 0:
                    shots_left = True
                    break

        # apply delay to all active units
        for ad in apply_delay:
            if ad[2] == 'groups':
                g_id, u_id = ad[3]
                obj = self.players[ad[1]]['groups'][g_id]['units'][u_id]
                self.players[ad[1]]['groups'][g_id][
                    'units'][u_id]['delay'] = obj['parameters']['delay_shoot']
            else:
                obj = self.players[ad[1]][ad[2]][ad[3]]
                obj = self.players[ad[1]][ad[2]][ad[3]][
                    'delay'] = obj['parameters']['delay_shoot']

        # Pretty print surviving units (can be returned to player)
        units = {'starters': [], 'enemies': []}

        for team, inv in [('starters', starters), ('enemies', enemies)]:
            for player, ids in inv.items():
                pl = self.players[player]
                for ind in ids:
                    if ind in pl['groups'].keys():
                        for unit in pl['groups'][ind]['units'].values():
                            units[team].append(unit['parameters']['name'])
                    elif ind in pl['transporter'].keys():
                        name = pl['transporter'][ind]['parameters']['name']
                        units[team].append(name)
                    elif ind in pl['buildings'].keys():
                        name = pl['buildings'][ind]['parameters']['name']
                        units[team].append(name)


        for team in ['starters', 'enemies']:
            occ = count(units[team])
            disp = []
            for u_type, num in occ.items():
                disp.append(str(num) + 'x ' + u_type)
            units[team] = ', '.join(disp)

        s = ','.join(starters.keys())
        e = ','.join(enemies.keys())
        msg_stack = {}

        # General message to all non-involved players
        title = 'Fight between %s and %s' % (s, e)
        msg = 'Total damage dealt:\n'
        msg += s + ': ' + str(total_damage['starters']) + '\n'
        msg += e + ': ' + str(total_damage['enemies']) + '\n'

        msg_stack['other'] = {'title': title, 'message': msg, 'popup': False}

        # Message to starters
        for player in starters.keys():
            title = 'Fight: You attacked %s!' % (e)
            msg = 'Total damage dealt:\n'
            msg += 'You: ' + str(total_damage['starters']) + '\n'
            msg += e + ': ' + str(total_damage['enemies']) + '\n'

            if total_damage['starters'] > 0:
                if units['enemies'] != '':
                    msg += '\nSurviving enemies:\n' + units['enemies']
                else:
                    msg += '\nYou have erradicated\nall opposing units!'

            try:
                occ = count(dead[player])
                disp = []
                for u_type, num in occ.items():
                    disp.append(str(num) + 'x ' + u_type)
                player_dead = ', '.join(disp)

                msg += '\nOur fallen heroes:\n' + player_dead
            except KeyError:
                pass

            msg_stack[player] = {'title': title, 'message': msg, 'popup': True}

        # Message to enemies
        for player in enemies.keys():
            title = 'Fight: You were attacked by %s!' % (s)
            msg = 'Total damage dealt:\n'
            msg += 'You: ' + str(total_damage['enemies']) + '\n'
            msg += s + ': ' + str(total_damage['starters']) + '\n'

            if total_damage['enemies'] > 0:
                if units['starters'] != '':
                    msg += '\nSurviving enemies:\n' + units['starters']
                else:
                    msg += '\nYou have erradicated\nall opposing units!'

            try:
                occ = count(dead[player])
                disp = []
                for u_type, num in occ.items():
                    disp.append(str(num) + 'x ' + u_type)
                player_dead = ', '.join(disp)

                msg += '\nOur fallen heroes:\n' + player_dead
            except KeyError:
                pass

            msg_stack[player] = {'title': title, 'message': msg, 'popup': True}

        return msg_stack

        '''
            # make message stack with events from fight
            msg_stack = {}
            enemy = enemies.keys()[0]
            starter = starter.keys()[0]
            msg = {}
            msg['title'] = 'Fight against {0}!'.format(enemy)
            msg['message'] = 'You made {0} damage,\n'.format(starter_damage)
            msg['message'] += '{0} made {1} damage.'.format(
                enemy, enemy_damage)
            msg['popup'] = True
            msg_stack[starter] = msg
            msg = {}
            msg['title'] = 'Fight against {0}!'.format(starter)
            msg['message'] = 'You made {0} damage,\n'.format(enemy_damage)
            msg['message'] += '{0} made {1} damage.'.format(
                starter, starter_damage)
            msg['popup'] = True
            msg_stack[enemy] = msg
            msg = {}
            msg['title'] = 'Fight between {0} & {1}!'.format(starter, enemy)
            msg['message'] = '{0} made {1} damage,\n'.format(
                starter, starter_damage)
            msg['message'] += '{0} made {1} damage.'.format(
                enemy, enemy_damage)
            msg['popup'] = False
            msg_stack['others'] = msg

            return msg_stack

        return {starter: {'title': 'Could not fight', 'message': '', 'popup': True}}
        '''
