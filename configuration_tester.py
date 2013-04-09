import wx, engine
import wx.lib.scrolledpanel as scrolled


class FightTester(wx.Dialog):
    def __init__(self, game_parameters):
        wx.Dialog.__init__(
            self, None, title='Uster Wars Fight Tester', size=(800, 600))
        self.game_parameters = game_parameters
        self.scroll_panel = scrolled.ScrolledPanel(self, -1, size=(780, 580))

        self.current_upgrades_1 = []
        self.current_upgrades_2 = []

        self.group1 = wx.TextCtrl(self.scroll_panel, -1, '0,0,0')
        self.group2 = wx.TextCtrl(self.scroll_panel, -1, '0,0,1')
        self.distance = wx.TextCtrl(self.scroll_panel, -1, '5')
        self.fight_btn = wx.Button(self.scroll_panel, -1, 'New Fight!')
        self.next_fight_btn = wx.Button(self.scroll_panel, -1, 'Next Fight!')

        self.group1_upgrades = wx.StaticText(self.scroll_panel, -1, '')
        self.group2_upgrades = wx.StaticText(self.scroll_panel, -1, '')

        self.add_unit_action_1 = wx.Button(
            self.scroll_panel, -1, 'Add Unit Action')
        self.add_unit_action_2 = wx.Button(
            self.scroll_panel, -1, 'Add Unit Action')
        self.clear_1 = wx.Button(self.scroll_panel, -1, 'Clear All')
        self.clear_2 = wx.Button(self.scroll_panel, -1, 'Clear All')

        self.result = wx.StaticText(self.scroll_panel, -1)

        self.fight_btn.Bind(wx.EVT_BUTTON, self.on_fight)
        self.next_fight_btn.Bind(wx.EVT_BUTTON, self.next_fight)

        self.add_unit_action_1.Bind(
            wx.EVT_BUTTON, lambda evt, ind=1: self.add_unit_action(evt, ind))
        self.add_unit_action_2.Bind(
            wx.EVT_BUTTON, lambda evt, ind=2: self.add_unit_action(evt, ind))
        self.clear_1.Bind(
            wx.EVT_BUTTON, lambda evt, ind=1: self.clear_all(evt, ind))
        self.clear_2.Bind(
            wx.EVT_BUTTON, lambda evt, ind=2: self.clear_all(evt, ind))

        self.init_layout()

    def init_layout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        fight_sizer = wx.BoxSizer(wx.HORIZONTAL)
        update_1 = wx.BoxSizer(wx.HORIZONTAL)
        update_2 = wx.BoxSizer(wx.HORIZONTAL)

        fight_sizer.Add(
            wx.StaticText(self.scroll_panel, -1, 'Group1:'), 0, wx.LEFT, 5)
        fight_sizer.Add(self.group1, 0, wx.LEFT, 5)
        fight_sizer.Add(
            wx.StaticText(self.scroll_panel, -1, 'Group2:'), 0, wx.LEFT, 5)
        fight_sizer.Add(self.group2, 0, wx.LEFT, 5)
        fight_sizer.Add(
            wx.StaticText(self.scroll_panel, -1, 'Distance'), 0, wx.LEFT, 5)
        fight_sizer.Add(self.distance, 0, wx.LEFT, 5)
        fight_sizer.Add(self.fight_btn, 0, wx.LEFT, 5)
        fight_sizer.Add(self.next_fight_btn, 0, wx.LEFT, 5)

        update_1.Add(
            wx.StaticText(self.scroll_panel, -1, 'Updates 1:'), 0, wx.LEFT, 5)
        update_1.Add(self.add_unit_action_1, 0, wx.LEFT, 5)
        update_1.Add(self.clear_1, 0, wx.LEFT, 5)
        update_1.Add(self.group1_upgrades, 0, wx.LEFT, 5)

        update_2.Add(
            wx.StaticText(self.scroll_panel, -1, 'Updates 2:'), 0, wx.LEFT, 5)
        update_2.Add(self.add_unit_action_2, 0, wx.LEFT, 5)
        update_2.Add(self.clear_2, 0, wx.LEFT, 5)
        update_2.Add(self.group2_upgrades, 0, wx.LEFT, 5)

        main_sizer.Add(fight_sizer, 0, wx.TOP, 20)
        main_sizer.Add(update_1, 0, wx.TOP, 20)
        main_sizer.Add(update_2, 0, wx.TOP, 20)

        main_sizer.Add(self.result, 0, wx.EXPAND)
        self.scroll_panel.SetupScrolling(True, True)

        self.SetSizer(main_sizer)
        self.update_upgrades()

        self.Layout()

    def on_fight(self, evt):
        group1 = [int(i) for i in self.group1.GetValue().split(',')]
        group2 = [int(i) for i in self.group2.GetValue().split(',')]
        distance = int(self.distance.GetValue())

        game = engine.MapWarfare(self.game_parameters)
        game.new_player('a', 1)
        game.new_player('b', 2)

        game.new_group('a', group1, 1)
        game.new_group('b', group2, 1)

        if self.current_upgrades_1:
            for upgrade in self.current_upgrades_1:
                for u_id in range(len(group1)):
                    if upgrade in game.players['a']['groups'][1]['units'][u_id]['parameters']['actions'].keys():
                        game.perform_unit_action('a', upgrade, 1, u_id)

        if self.current_upgrades_2:
            for upgrade in self.current_upgrades_2:
                for u_id in range(len(group2)):
                    if upgrade in game.players['b']['groups'][1]['units'][u_id]['parameters']['actions'].keys():
                        game.perform_unit_action('b', upgrade, 1, u_id)

        # ids are one because of headquarters, distance is 5
        game.fight({'a': [1]}, {'b': [1]}, distance)

        res = '\nFIGHT\n\nGroup 1 lifes:\n'
        try:
            for unit in game.players['a']['groups'][1]['units'].values():
                u_p = unit['parameters']
                res += ' -life: {0}/{1}, shield: {2}\n'.format(
                    u_p['life'], u_p['max_life'], u_p['shield'])
        except KeyError:
            res += 'all dead\n'

        res += '\n\nGroup 2 lifes:\n'
        try:
            for unit in game.players['b']['groups'][1]['units'].values():
                u_p = unit['parameters']
                res += ' -life: {0}/{1}, shield: {2}\n'.format(
                    u_p['life'], u_p['max_life'], u_p['shield'])
        except KeyError:
            res += 'all dead\n'

        self.result.SetLabel(res)
        self.scroll_panel.FitInside()

        # Run a few ticks (no delay for units...)
        for i in range(50):
            game.on_tick()
        # Save current state of game (for next fight)
        self.game = game

    def next_fight(self, evt):
        if hasattr(self, 'game'):
            game = self.game
            distance = int(self.distance.GetValue())
            game.fight({'a': [1]}, {'b': [1]}, distance)
            res = '\nFIGHT\n\nGroup 1 lifes:\n'
            try:
                for unit in game.players['a']['groups'][1]['units'].values():
                    u_p = unit['parameters']
                    res += ' -life: {0}/{1}, shield: {2}\n'.format(
                        u_p['life'], u_p['max_life'], u_p['shield'])
            except KeyError:
                res += 'all dead\n'

            res += '\n\nGroup 2 lifes:\n'
            try:
                for unit in game.players['b']['groups'][1]['units'].values():
                    u_p = unit['parameters']
                    res += ' -life: {0}/{1}, shield: {2}\n'.format(
                        u_p['life'], u_p['max_life'], u_p['shield'])
            except KeyError:
                res += 'all dead\n'

            self.result.SetLabel(res)
            self.scroll_panel.FitInside()

            # Run a few ticks (no delay for units...)
            for i in range(50):
                game.on_tick()

            self.game = game

    def clear_all(self, evt, group):
        if group == 1:
            self.current_upgrades_1 = []
        else:
            self.current_upgrades_2 = []
        self.update_upgrades()

    def update_upgrades(self):
        self.group2_upgrades.SetLabel(
            ', '.join([str(c) for c in self.current_upgrades_2]))
        self.group1_upgrades.SetLabel(
            ', '.join([str(c) for c in self.current_upgrades_1]))

    def add_unit_action(self, evt, group):
        if group == 1:
            units = [int(i) for i in self.group1.GetValue().split(',')]
        else:
            units = [int(i) for i in self.group2.GetValue().split(',')]

        # get all unit actions
        all_unit_actions = []

        def recursive_enlist(actions):
            for name, action in actions.items():
                all_unit_actions.append(name)
                for act in action['actions']:
                    try:
                        sub_actions = act['changes']['actions']
                        recursive_enlist(sub_actions)
                    except KeyError:
                        pass

        units = list(set(units))
        for u_id in units:
            unit_p = self.game_parameters['unit_parameters'][
                u_id]['basic_parameters']
            recursive_enlist(unit_p['actions'])

        dlg = wx.SingleChoiceDialog(
            self, 'Take care: Upgrades which require other upgrades have to be added after the original upgrade...', 'Choose a Upgrade',
            choices=all_unit_actions)

        if dlg.ShowModal():
            unit_action = dlg.GetStringSelection()
            if group == 1:
                self.current_upgrades_1.append(unit_action)
            elif group == 2:
                self.current_upgrades_2.append(unit_action)

            self.update_upgrades()
