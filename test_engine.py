import unittest
import time
import random
import pickle
import copy
import engine

filepath = '2.4.army'
game_parameters = pickle.load(open(filepath, "r"))


class TestBasicFunctions(unittest.TestCase):

    def test_player_creation(self):
        tests = ['uuu', 'alllll', 'All', '00', 'oo']

        for name in tests:
            game = engine.MapWarfare(game_parameters)
            game.new_player(name, 1, False)
            self.assertTrue(type(game.players[name]) == dict)
            for empty in ('groups', 'transporter', 'cards'):
                self.assertDictEqual(game.players[name][empty], {})

            # Check if headquarters was created
            self.assertEqual(game.players[name]['buildings'][0]
                             ['parameters']['name'], 'Hauptquartier')

    def test_group_creation(self):
        tests = [[0, 0, 0, 1], [0, 0, 0, 0, 0, 0, 0, 0], [1, 1, 1]]

        for group in tests:
            game = engine.MapWarfare(game_parameters)
            game.new_player('player1', 1, False)
            acc = 1000000
            game.players['player1']['account'] = acc
            # Create the group
            game.new_group('player1', group, 1)
            # get the group
            res_group = game.players['player1']['groups'][1]
            # what would be expected?
            u_id = 0
            total_price = 0
            exp_u = {}
            for u_type in group:
                params = game_parameters[
                    'unit_parameters'][u_type]['basic_parameters']
                total_price += params['price']
                new_unit = {'age': 0, 'total_damage': 0,
                            'protected': False, 'delay': 0, 'building': -1  # , 'parameters': params
                            }
                exp_u[u_id] = new_unit
                u_id += 1

            exp = {'name': '', 'transporter': -1}
            for param, value in exp.items():
                self.assertEqual(res_group[param], value)

            self.assertEqual(len(res_group['units'].keys()), len(exp_u.keys()))

            acc_exp = acc - total_price

            self.assertEqual(game.players['player1']['account'], acc_exp)
            for u_id, unit in res_group['units'].items():
                for param, value in exp_u[u_id].items():
                    self.assertEqual(res_group['units'][u_id][param], value)


class TestMoveIntoSector(unittest.TestCase):

    def test_single_move_group(self):

        test_groups = [[0, 0, 0], [0], [0, 1], [1, 1, 1, 1, 1, 1]]

        for group in test_groups:
            game = engine.MapWarfare(game_parameters)
            game.new_player('a', 1, False)
            game.new_group('a', group, 1, costs = False)

            self.assertEqual(game.players['a']['groups'][1]['sector'], 1)

            random_sector = random.randrange(1, 10)
            game.move_into_sector('a', 1, random_sector)
            self.assertEqual(
                game.players['a']['groups'][1]['sector'], random_sector)
            for unit in game.players['a']['groups'][1]['units'].values():
                self.assertEqual(unit['delay'], game_parameters['unit_parameters'][unit['parameters']
                                 ['id']]['basic_parameters']['delay_walk'])

    def test_single_move_transporter(self):

        game = engine.MapWarfare(game_parameters)
        game.new_player('a', 1, False)
        game.new_transporter('a', 0, 1, '', False)

        self.assertEqual(game.players['a']['transporter'][1]['sector'], 1)

        random_sector = random.randrange(1, 10)
        game.move_into_sector('a', 1, random_sector)
        trans = game.players['a']['transporter'][1]
        self.assertEqual(trans['sector'], random_sector)
        self.assertEqual(trans['delay'], game_parameters['transport_parameters'][trans[
                         'parameters']['id']]['basic_parameters']['delay_walk'])


class TestSimpleActions(unittest.TestCase):

    def test_group_creation(self):
        time.sleep(0.01)
        test_groups = [
            [0, 0, 0, 0, 0, 1], [0, 0, 1, 1, 1, 1], [0, 0, 0, 0, 0, 0, 0, 0,
                                                     0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

        for group in test_groups:
            action = {'type': 'new', 'level': 'groups',
                      'parameters': group, 'target': 'own'}

            game = engine.MapWarfare(game_parameters)
            game.new_player('a', 1, False)
            account_before = game.players['a']['account']
            game.perform_action('a', action)
            self.assertEqual(
                account_before, game.players['a']['account'], str(group))
            # Check if group number 1 (hq is 0) has the right content
            all_units = []
            for unit in game.players['a']['groups'][1]['units'].values():
                all_units.append(unit['parameters']['id'])

            self.assertEqual(sorted(all_units), sorted(group))

    def test_healing(self):
        print 'IMPLEMENT Test: Healing/Doctor'

    def test_unit_actions(self):
        print 'IMPLEMENT Test: unit actions'

    def test_action_player(self):
        tests = [
            ('account', 100),
            ('victory_points', 10),
            ('account', 99.0),
            ('victory_points', 11.0),
        ]

        for param, value in tests:
            game = self.construct_game()
            selection = {
                'own_selection': False, 'enemy': 'b', 'enemy_selection': False}
            action = {
                'type': 'change', 'target': 'own', 'level': 'player', 'random': 0,
                'selection': selection, 'changes': {param: value}}

            param_before = game.players['a'][param]
            s = game.perform_action('a', action)
            self.assertTrue(s)
            self.assertEqual(game.players['a'][param], param_before + value)

    def test_change_normal(self):

        # IMPLEMENT: Test adding unit actions.
        
        test_changes = [{'attack_min': 100, 'attack_max': -10},
                        {'max_life': 100, 'attack_max': -2, 'life': 50},
                        {'elite': 1, 'delay_shoot': -3, 'delay_walk': -2},
                        {'attack_max': 20, 'attack_min': 10, 'num_enemies': 3, 'life': -10, 'shoot_dist': 10,
                            'walk_dist': 13, 'delay_shoot': 10, 'delay_walk': 10, 'elite': 0},
                        {'shield_factor': 0.113453626, 'attack_max': -1, 'attack_min': -1, 
                            'num_enemies': -1, 'life': -1, 'shoot_dist': -1,
                            'walk_dist': -1, 'delay_shoot': -2, 'delay_walk': -2}
                        ]

        selection = {'own_selection': [(1, 0), (1, 1), (1, 2)],
                     'enemy': 'b', 'enemy_selection': [1]}

        par = game_parameters['unit_parameters']

        for change in test_changes:
            # Test change all own
            action = {
                'type': 'change', 'target': 'own', 'level': 'id', 'random': 0, 'num_units': 'all',
                'changes': change}

            game = self.construct_game()

            success = game.perform_action(
                'a', action, copy.deepcopy(selection))
            self.assertTrue(success)
            for param, val in change.items():
                # a changes
                for group in game.players['a']['groups'].values():
                    for unit in group['units'].values():
                        exp = par[unit['parameters'][
                            'id']]['basic_parameters'][param] + val
                        self.assertEqual(exp, unit['parameters'][param])

                # b not affected
                for group in game.players['b']['groups'].values():
                    for unit in group['units'].values():
                        exp = par[unit[
                            'parameters']['id']]['basic_parameters'][param]
                        self.assertEqual(exp, unit['parameters'][param])

            # Test Change all enemy
            action = {
                'type': 'change', 'target': 'enemy', 'level': 'id', 'random': 0, 'num_units': 'all',
                'changes': change}

            game = self.construct_game()

            success = game.perform_action(
                'a', action, copy.deepcopy(selection))
            self.assertTrue(success)
            for param, val in change.items():
                # a changes
                for group in game.players['b']['groups'].values():
                    for unit in group['units'].values():
                        exp = par[unit['parameters'][
                            'id']]['basic_parameters'][param] + val
                        self.assertEqual(exp, unit['parameters'][param])
                # b not affected
                for group in game.players['a']['groups'].values():
                    for unit in group['units'].values():
                        exp = par[unit[
                            'parameters']['id']]['basic_parameters'][param]
                        self.assertEqual(exp, unit['parameters'][param])

            # Test Change own selection, not limited by number
            action = {
                'type': 'change', 'target': 'own', 'level': 'id', 'random': 0, 'num_units': 3,
                'changes': change}

            game = self.construct_game()

            success = game.perform_action('a', action, copy.deepcopy(selection))
            self.assertTrue(success)
            for param, val in change.items():
                # a changes group 1
                for unit in game.players['a']['groups'][1]['units'].values():
                    exp = par[unit['parameters']['id']
                              ]['basic_parameters'][param] + val
                    self.assertEqual(unit['parameters'][param], exp)

                # group 2 not affected
                for unit in game.players['a']['groups'][2]['units'].values():
                    exp = par[unit['parameters']['id']
                              ]['basic_parameters'][param]
                    self.assertEqual(exp, unit['parameters'][param])

                # b not affected
                for group in game.players['b']['groups'].values():
                    for unit in group['units'].values():
                        exp = par[unit[
                            'parameters']['id']]['basic_parameters'][param]
                        self.assertEqual(exp, unit['parameters'][param])

            # Test Change enemy selection, not limited by number
            action = {
                'type': 'change', 'target': 'enemy', 'level': 'id', 'random': 0, 'num_units': 3,
                'changes': change}

            game = self.construct_game()

            success = game.perform_action(
                'a', action, copy.deepcopy(selection))
            self.assertTrue(success)
            for param, val in change.items():
                # a changes group 1
                for unit in game.players['b']['groups'][1]['units'].values():
                    exp = par[unit['parameters']['id']
                              ]['basic_parameters'][param] + val
                    self.assertEqual(exp, unit['parameters'][param])

                # group 2 not affected
                for unit in game.players['b']['groups'][2]['units'].values():
                    exp = par[unit['parameters']['id']
                              ]['basic_parameters'][param]
                    self.assertEqual(exp, unit['parameters'][param])

                # b not affected
                for group in game.players['a']['groups'].values():
                    for unit in group['units'].values():
                        exp = par[unit[
                            'parameters']['id']]['basic_parameters'][param]
                        self.assertEqual(exp, unit['parameters'][param])

            # Test Change own selection, limited by number
            action = {'type': 'change', 'target': 'own',
                      'level': 'id', 'random': 0, 'num_units': 1, 'changes': change}

            game = self.construct_game()
            success = game.perform_action(
                'a', action, copy.deepcopy(selection))
            self.assertTrue(success)
            # check number of changed units
            param = change.keys()[0]
            num_changed = 0
            # b not affected
            for group in game.players['a']['groups'].values():
                for unit in group['units'].values():
                    orig = par[unit['parameters']['id']
                               ]['basic_parameters'][param]
                    if unit['parameters'][param] != orig:
                        num_changed += 1

            self.assertEqual(num_changed, 1, param)

            # Test Change own selection, limited by number
            action = {
                'type': 'change', 'target': 'enemy', 'level': 'id', 'random': 0, 'num_units': 2,
                'changes': change}

            game = self.construct_game()
            success = game.perform_action(
                'a', action, copy.deepcopy(selection))
            self.assertTrue(success)
            # check number of changed units
            param = change.keys()[0]
            num_changed = 0
            # b not affected
            for group in game.players['b']['groups'].values():
                for unit in group['units'].values():
                    orig = par[unit['parameters']['id']
                               ]['basic_parameters'][param]
                    if unit['parameters'][param] != orig:
                        num_changed += 1

            self.assertEqual(num_changed, 2, param)

            # Test change self
            action = {
                'type': 'change', 'target': 'self', 'level': 'id', 'random': 0,
                'changes': change}

            game = self.construct_game()
            success = game.perform_action(
                'a', action, copy.deepcopy(selection), o_id=1, u_id=1)
            self.assertTrue(success)
            # check number of changed units
            param = change.keys()[0]
            num_changed = 0

            # only one unit affected
            for group in game.players['a']['groups'].values():
                for unit in group['units'].values():
                    orig = par[unit['parameters']['id']
                               ]['basic_parameters'][param]
                    if unit['parameters'][param] != orig:
                        num_changed += 1

            self.assertEqual(num_changed, 1)

            # test parameters
            for param, val in change.items():
                # a changes group 1
                unit = game.players['a']['groups'][1]['units'][1]
                exp = par[unit['parameters']['id']][
                    'basic_parameters'][param] + val
                self.assertEqual(exp, unit['parameters'][param])

            # Test time-depended upgrade
            num_rounds = random.randrange(1, 100)
            action = {
                'type': 'change', 'target': 'self', 'level': 'id', 
                'random': 0, 'changes': {'time_dependent_actions': 
                    {num_rounds:
                        [{
                        'type': 'change', 'target': 'self', 'level': 'id', 
                        'random': 0,'changes': change
                        }]
                    }
                }}

            game = self.construct_game()

            # Run 9 ticks (10th round)
            for i in range(9):
                game.on_tick()

            success = game.perform_action(
                'a', action, copy.deepcopy(selection), o_id=1, u_id=1)
            self.assertTrue(success)

            # Run num_rounds ticks
            for i in range(num_rounds):
                game.on_tick()

            # Save the state before, unit will be upgraded at end of tick
            before = copy.deepcopy(game.players['a']['groups'][1]['units'][1])
            game.on_tick()

            # test all parameters
            for param, val in change.items():
                # a changes group 1
                unit = game.players['a']['groups'][1]['units'][1]
                exp = before['parameters'][param] + val
                self.assertEqual(exp, unit['parameters'][param])


    def construct_game(self):
        game = engine.MapWarfare(game_parameters)
        game.new_player('a', 1, False)
        game.new_player('b', 2, False)

        game.new_group('a', [0, 2, 3], 1, costs=False)
        game.new_group('a', [0, 2, 3], 1, costs=False)
        game.new_group('a', [0, 2, 3], 1, costs=False)

        game.new_group('b', [0, 2, 3], 1, costs=False)
        game.new_group('b', [0, 2, 3], 1, costs=False)
        game.new_group('b', [0, 2, 3], 1, costs=False)

        return game


if __name__ == '__main__':
    unittest.main()
