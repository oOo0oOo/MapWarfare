import wx
import time
import os
import pickle
from copy import deepcopy
import wx.lib.scrolledpanel as scrolled
from configuration_tester import FightTester as Tester

class ConfigurationHelper(wx.Dialog):
    def __init__(self, filename = '', game_parameters = {}):
        wx.Dialog.__init__(
            self, None, title='Uster Wars Configuration Helper', size=(1330, 700))
        self.top_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_panel = scrolled.ScrolledPanel(
            self, -1, size=(1300, 670))

        if game_parameters:
            self.game_parameters = deepcopy(game_parameters)

        elif filename:
            self.game_parameters = pickle.load(open(filename, "r"))

        else:
            # All game engine parameters
            engine_params = {
                # Initial duration of one tick in seconds
                #(can be changed during game)
                'tick_duration': 10,
                # How much $ in initial account
                'start_account': 300,
                # These are the sectors defined at the top
                'all_sectors': {1: {'weight':0.5, 'victory':0}, 2: {'weight':0.5,'victory':0}, 3: {'weight':0.5, 'victory':0}},
                # Rewards ($)
                'per_sector_per_tick': 3,
                'sector_takeover': 250,
                'constant_per_tick': 5,
                # Take over factor x: Player has to have x times the life
                # in a sector to overtake it.
                # E.g. Take over factor = 1.5; A has 1200 life (1 HQ plus some units) in sector,
                # B has to have at least 1.5 * 1200 = 1800 life in
                # sector to take over.
                'take_over_factor': 1.5,
                # up to how many percent less damage: e.g. 0.4 = 0% -
                # 40% less damage if protected
                'protection_effect': 0.4,
                # how many rounds the units can not act when being protected
                # use 0 if immediately, 1 if in the next round and 2 if
                # one round delayed
                'protection_in': 2,
                'protection_out': 1,
                'delay_damage': 0.0,
                'extra_shoot_dist': 2,
                'max_victory_diff': 50
            }

            self.game_parameters = {
                'unit_parameters': {}, 'transport_parameters': {},
                'building_parameters': {}, 'engine_parameters': engine_params,
                'card_parameters': {}}


        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.AddSpacer(10)

        self.card_btns = {}
        self.unit_btns = {}
        self.unit_sizer = wx.FlexGridSizer(3, 10)

        self.transporter_btns = {}
        self.transporter_sizer = wx.FlexGridSizer(3, 10)

        self.building_btns = {}
        self.building_sizer = wx.FlexGridSizer(3, 10)

        self.card_btns = {}
        # Card sizers holds all sizers necessary for the display of categories
        self.card_sizers = {}
        # Texts are the labels for the different card categories
        self.texts = {}
        self.card_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.update_buttons()

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_unit_btn = wx.Button(self.scroll_panel, -1, 'Add New Unit')
        self.add_transporter_btn = wx.Button(
            self.scroll_panel, -1, 'Add New Transporter')
        self.add_building_btn = wx.Button(
            self.scroll_panel, -1, 'Add New Building')

        self.add_unit_btn.Bind(wx.EVT_BUTTON, self.add_unit)
        self.add_transporter_btn.Bind(wx.EVT_BUTTON, self.add_transporter)
        self.add_building_btn.Bind(wx.EVT_BUTTON, self.add_building)

        btn_sizer.Add(self.add_unit_btn)
        btn_sizer.Add(self.add_transporter_btn)
        btn_sizer.Add(self.add_building_btn)
        btn_sizer.AddSpacer(25)

        save_btn = wx.Button(
            self.scroll_panel, -1, 'Save configuration to file')
        save_btn.Bind(wx.EVT_BUTTON, self.save_configuration)
        btn_sizer.Add(save_btn)

        load_btn = wx.Button(
            self.scroll_panel, -1, 'Load configuration from file')
        load_btn.Bind(wx.EVT_BUTTON, self.load_configuration)
        btn_sizer.Add(load_btn)

        self.main_sizer.Add(btn_sizer)
        self.main_sizer.AddSpacer(25)

        engine_btn = wx.Button(self.scroll_panel, -1, 'Engine Parameters')
        self.main_sizer.Add(engine_btn)
        engine_btn.Bind(wx.EVT_BUTTON, self.on_engine_parameters)

        self.main_sizer.AddSpacer(15)

        sector_btn = wx.Button(self.scroll_panel, -1, 'Sector Weights')
        self.main_sizer.Add(sector_btn)
        sector_btn.Bind(wx.EVT_BUTTON, self.on_sector)

        self.main_sizer.AddSpacer(15)

        add_cateogry_btn = wx.Button(
            self.scroll_panel, -1, 'Add Card Category')
        self.main_sizer.Add(add_cateogry_btn)
        add_cateogry_btn.Bind(wx.EVT_BUTTON, self.add_card_category)

        self.main_sizer.AddSpacer(15)

        add_card_btn = wx.Button(self.scroll_panel, -1, 'Add Card')
        self.main_sizer.Add(add_card_btn)
        add_card_btn.Bind(wx.EVT_BUTTON, self.add_card)

        self.main_sizer.AddSpacer(25)
        self.main_sizer.Add(wx.StaticText(self.scroll_panel, -1, 'All Units'))
        self.main_sizer.Add(self.unit_sizer)
        self.main_sizer.AddSpacer(25)
        self.main_sizer.Add(
            wx.StaticText(self.scroll_panel, -1, 'All Transporter'))
        self.main_sizer.Add(self.transporter_sizer)
        self.main_sizer.AddSpacer(25)
        self.main_sizer.Add(
            wx.StaticText(self.scroll_panel, -1, 'All Buildings'))
        self.main_sizer.Add(self.building_sizer)

        # A sizer for cards
        self.main_sizer.AddSpacer(25)
        self.main_sizer.Add(wx.StaticText(self.scroll_panel, -1, 'All Cards'))
        self.main_sizer.Add(self.card_sizer)

        self.main_sizer.AddSpacer(30)

        test_btn = wx.Button(self.scroll_panel, -1, 'Test Fight')
        test_btn.Bind(wx.EVT_BUTTON, self.test_configuration)
        self.main_sizer.Add(test_btn)

        start_btn = wx.Button(self.scroll_panel, -1, 'Start Game')
        start_btn.Bind(wx.EVT_BUTTON, self.start_game)
        self.main_sizer.Add(start_btn)

        self.scroll_panel.SetSizer(self.main_sizer)
        self.scroll_panel.SetupScrolling(True, True)
        self.top_sizer.Add(self.scroll_panel)
        self.SetSizer(self.top_sizer)
        self.Layout()
        self.Show()

    def test_configuration(self, evt):
        dlg = Tester(self.game_parameters)
        dlg.ShowModal()

    def start_game(self, evt):
        self.EndModal(True)

    def save_configuration(self, evt):
        dlg = wx.FileDialog(
            self, 'Choose a filename', '', '', '*.army', wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            filepath = os.path.join(dirname, filename)
            pickle.dump(self.game_parameters, open(filepath, "w"))

    def load_configuration(self, evt):
        dlg = wx.FileDialog(self, 'Choose a file', '', '', '*.army', wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            filepath = os.path.join(dirname, filename)
            self.game_parameters = pickle.load(open(filepath, "r"))

            try:
                self.game_parameters['engine_parameters']['delay_damage']
            except KeyError:
                self.game_parameters['engine_parameters']['delay_damage'] = 0.0

            try:
                self.game_parameters['engine_parameters']['extra_shoot_dist']
            except KeyError:
                self.game_parameters['engine_parameters']['extra_shoot_dist'] = 2

            try:
                self.game_parameters['engine_parameters']['max_victory_diff']
            except KeyError:
                self.game_parameters['engine_parameters']['max_victory_diff'] = 50

            self.update_buttons()

    def on_engine_parameters(self, evt):
        dlg = EngineParameters(self.game_parameters['engine_parameters'])
        dlg.ShowModal()
        dlg.Destroy()

    def on_sector(self, evt):
        dlg = Sectors(self.game_parameters['engine_parameters']['all_sectors'])
        dlg.ShowModal()
        dlg.Destroy()

    def update_buttons(self):
        self.unit_sizer.Clear()
        self.transporter_sizer.Clear()
        self.building_sizer.Clear()
        self.card_sizer.Clear()

        for btn in self.unit_btns.values():
            btn.Destroy()

        for btn in self.transporter_btns.values():
            btn.Destroy()

        for btn in self.building_btns.values():
            btn.Destroy()

        for cat in self.card_btns.values():
            for btn in cat.values():
                btn.Destroy()

        for text in self.texts.values():
            text.Destroy()

        self.unit_btns = {}
        self.transporter_btns = {}
        self.building_btns = {}
        self.card_btns = {}
        self.card_sizers = {}

        for u_id, unit in self.game_parameters['unit_parameters'].items():
            self.unit_btns[u_id] = wx.Button(self.scroll_panel, -1, unit['basic_parameters']['name'] + ': ' + str(unit[
                                             'basic_parameters']['id']), name=str(u_id))
            self.unit_sizer.Add(self.unit_btns[u_id])
            self.unit_btns[u_id].Bind(wx.EVT_BUTTON, self.on_unit_click)

        for t_id, transporter in self.game_parameters['transport_parameters'].items():
            self.transporter_btns[t_id] = wx.Button(
                self.scroll_panel, -1, transporter['basic_parameters']['name'] + ': ' + str(transporter['basic_parameters']['id']), name=str(t_id))
            self.transporter_sizer.Add(self.transporter_btns[t_id])
            self.transporter_btns[t_id].Bind(wx.EVT_BUTTON,
                                             self.on_transporter_click)

        for b_id, building in self.game_parameters['building_parameters'].items():
            self.building_btns[b_id] = wx.Button(
                self.scroll_panel, -1, building['basic_parameters']['name'] + ': ' + str(building['basic_parameters']['id']), name=str(b_id))
            self.building_sizer.Add(self.building_btns[b_id])
            self.building_btns[b_id].Bind(wx.EVT_BUTTON,
                                          self.on_building_click)

        for cat, cards in self.game_parameters['card_parameters'].items():
            self.card_sizers[cat] = wx.BoxSizer(wx.VERTICAL)
            self.card_sizers[cat].SetMinSize((200, 50))

            self.texts[cat] = wx.StaticText(
                self.scroll_panel, -1, 'Category {0}$'.format(cat))
            self.card_sizers[cat].Add(self.texts[cat])

            count = 0
            self.card_btns[cat] = {}
            for card in cards:
                self.card_btns[cat][count] = wx.Button(
                    self.scroll_panel, -1, card['title'], name=str(cat) + '<>' + str(count))
                self.card_sizers[cat].Add(self.card_btns[cat][count])
                self.card_btns[cat][count].Bind(
                    wx.EVT_BUTTON, self.on_card_click)
                count += 1

            self.card_sizer.Add(self.card_sizers[cat])

        self.scroll_panel.FitInside()

    def add_transporter(self, evt):
        template_transporter = {
            'basic_parameters': {'id': 0, 'name': 'transporter_name', 'transports': 'soldier',
                                 'capacity': 0, 'attack_max': 0, 'attack_min': 0, 'num_enemies': 0, 'life': 0, 'max_life': 0,
                                 'shield': 0, 'shield_factor': 0, 'delay_in': 0, 'delay_out': 0, 'delay_shoot': 0, 'delay_walk': 0,
                                 'shoot_dist': 0, 'walk_dist': 0, 'elite': 0, 'price': 0, 'actions': {'Dummy (delete this)':
                               {'price': 0, 'delay': 0, 'num_uses': 0, 'category': 'standard', 'actions': []}}
            },

            'elite_parameters': {'ticks': {0: []}, 'damage': {0: []}}
        }
        all_ind = self.game_parameters['transport_parameters'].keys()
        if all_ind:
            new_ind = max(all_ind) + 1
        else:
            new_ind = 0

        template_transporter['basic_parameters']['id'] = new_ind

        self.game_parameters['transport_parameters'][
            new_ind] = template_transporter

        self.update_buttons()

    def add_card_category(self, evt):
        dlg = wx.TextEntryDialog(
            self, 'How much will the cards in the new category cost?', 'Card Price')
        if dlg.ShowModal() == wx.ID_OK:
            amount = int(dlg.GetValue())
            self.game_parameters['card_parameters'][amount] = []
            self.update_buttons()

    def add_card(self, evt):
        template_card = {'title': 'Unnamed Card', 'description': 'Description', 'num_cards': 1, 'actions': []
                         }

        categories = [str(n) for n in self.game_parameters[
                      'card_parameters'].keys()]
        dlg = wx.SingleChoiceDialog(self, 'Add card to which card deck?',
                                    'Select Card Deck', choices=categories)
        if dlg.ShowModal() == wx.ID_OK:
            category = int(dlg.GetStringSelection())
            self.game_parameters['card_parameters'][
                category].append(template_card)

            self.update_buttons()

    def add_unit(self, evt):
        template_unit = {
            'basic_parameters': {'id': 1, 'name': 'unit_name', 'unit_type': 'soldier', 'attack_max': 0, 'attack_min': 0,
                                 'num_enemies': 0, 'life': 0, 'max_life': 0, 'shield': 0, 'shield_factor': 0,
                                 'shoot_dist': 0, 'walk_dist': 0, 'delay_shoot': 0, 'delay_walk': 0,
                                 'elite': 0, 'price': 0, 'actions': {'Dummy (delete this)':
                        {'price': 0, 'delay': 0, 'category':
                         'standard', 'num_uses': 0, 'actions': []}
                                 }
            },

            'elite_parameters': {'ticks': {0: []}, 'damage': {0: []}}
        }
        all_ind = self.game_parameters['unit_parameters'].keys()
        if all_ind:
            new_ind = max(all_ind) + 1
        else:
            new_ind = 0

        template_unit['basic_parameters']['id'] = new_ind

        self.game_parameters['unit_parameters'][new_ind] = template_unit

        self.update_buttons()

    def add_building(self, evt):
        template_building = {
            'basic_parameters': {'id': 0, 'name': 'building_name', 'enter': 'soldier',
                                 'capacity': 0, 'attack_max': 0, 'attack_min': 0, 'num_enemies': 0, 'life': 0, 'max_life': 0,
                                 'shield': 0, 'shield_factor': 0, 'delay_in': 0, 'delay_out': 0, 'shoot_dist': 0,
                                 'delay_shoot': 0, 'price': 0, 'shop_units': [0], 'shop_transporter': [0],
                                 'elite': 0, 'actions': {'Dummy (delete this)': {'price': 0, 'delay': 0, 'category': 'standard', 'num_uses': 0, 'actions': []}}
                                 },

            'elite_parameters': {'ticks': {0: []}, 'damage': {0: []}}
        }
        all_ind = self.game_parameters['building_parameters'].keys()
        if all_ind:
            new_ind = max(all_ind) + 1
        else:
            new_ind = 0

        template_building['basic_parameters']['id'] = new_ind

        self.game_parameters['building_parameters'][
            new_ind] = template_building

        self.update_buttons()

    def on_unit_click(self, evt):
        ind = int(evt.GetEventObject().GetName())
        unit = self.game_parameters['unit_parameters'][ind]
        dlg = DetailPage(unit)
        ret = dlg.ShowModal()
        dlg.Destroy()
        # Delete unit if not ret == True
        if not ret:
            del self.game_parameters['unit_parameters'][ind]

        self.update_buttons()

    def on_card_click(self, evt):
        category, number = evt.GetEventObject().GetName().split('<>')

        dlg = CardPage(self.game_parameters['card_parameters'][int(
            category)][int(number)])
        dlg.ShowModal()
        dlg.Destroy()

        self.update_buttons()

    def on_transporter_click(self, evt):
        ind = int(evt.GetEventObject().GetName())
        transporter = self.game_parameters['transport_parameters'][ind]
        dlg = DetailPage(transporter)
        ret = dlg.ShowModal()
        dlg.Destroy()
        if not ret:
            del self.game_parameters['transport_parameters'][ind]
        self.update_buttons()

    def on_building_click(self, evt):
        ind = int(evt.GetEventObject().GetName())
        building = self.game_parameters['building_parameters'][ind]
        dlg = DetailPage(building)
        ret = dlg.ShowModal()
        dlg.Destroy()
        if not ret:
            del self.game_parameters['building_parameters'][ind]
        self.update_buttons()


class ActionDetail(wx.Dialog):
    def __init__(self, action):
        wx.Dialog.__init__(self, None, -1, 'Action Details', size=(664, 468))
        self.action = action
        self.sub_elements = {}

        try:
            self.action['changes']
            self.is_change = True
        except KeyError:
            self.is_change = False

        choices = {
        'type': ['new', 'change'],
        'target': ['own', 'enemy'],
        'level': ['id', 'groups', 'buildings', 'transporter', 'player'],
        'num_units': False, 'random': False

        }

        for param, value in action.items():
            if param not in ('changes'):
                # Create the sizer, label and textcntrl
                this = []
                this.append(wx.BoxSizer(wx.HORIZONTAL))
                this.append(wx.StaticText(self, -1, param))
                if choices[param]:
                    this.append(wx.ComboBox(self, size=(100, 20), choices=choices[param]))
                    this[2].SetStringSelection(value)
                else:
                    this.append(wx.TextCtrl(self, -1, str(value), size=(40, 20)))
                
                # put them in order, add spacer and add to main sizer
                this[0].Add(this[1])
                this[0].AddSpacer(10)
                this[0].Add(this[2])
                # Add to sub_element dictionary
                self.sub_elements[param] = this

        self.add_btn = wx.Button(self, -1, 'Add Parameter')
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        self.exit_btn = wx.Button(self, -1, 'Exit and Save')
        self.exit_btn.Bind(wx.EVT_BUTTON, self.on_exit)
        self.changes_sizer = wx.BoxSizer(wx.VERTICAL)
        self.init_layout()

    def init_layout(self):
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        for param in self.sub_elements.values():
            main_sizer.Add(param[0])

        main_sizer.Add(self.exit_btn)
        main_sizer.Add(self.add_btn)

        top_sizer.Add(main_sizer)
        top_sizer.AddSpacer(15)
        top_sizer.Add(self.changes_sizer)

        self.SetSizer(top_sizer)
        self.update_changes()

    def update_changes(self):
        if self.is_change:
            self.changes_sizer.Clear(True)
            self.changes = {}
            for param, value in sorted(self.action['changes'].items()):
                # Create the sizer, label and textcntrl
                this = []
                this.append(wx.BoxSizer(wx.HORIZONTAL))
                this.append(wx.StaticText(self, -1, str(param)))
                this.append(wx.TextCtrl(self, -1, str(value), size=(40, 20)))
                this.append(wx.Button(self, -1, 'Remove', name=str(param)))
                this[3].Bind(wx.EVT_BUTTON, self.on_remove)

                # put them in order, add spacer and add to main sizer
                this[0].Add(this[1])
                this[0].AddSpacer(10)
                this[0].Add(this[2])
                this[0].AddSpacer(10)
                this[0].Add(this[3])
                self.changes_sizer.Add(this[0])
                # Add to sub_element dictionary
                self.changes[param] = this

        self.Layout()

    def on_add(self, evt):
        choices = [
            'max_life', 'life', 'shield', 'capacity', 'delay_in', 'delay_out', 'attack_min', 'attack_max',
            'num_enemies', 'shield_factor', 'shoot_dist', 'delay_shoot', 'walk_dist', 'delay_walk', 'elite', 'account']

        dlg = wx.SingleChoiceDialog(
            self, 'Which parameter do you want to add?',
            'Add Parameter', choices=choices)
        if dlg.ShowModal():
            param = dlg.GetStringSelection()
            self.action['changes'][param] = 0
            self.update_changes()

    def on_remove(self, evt):
        param = evt.GetEventObject().GetName()
        del self.action['changes'][param]
        self.update_changes()

    def on_exit(self, evt):
        for param, val in self.sub_elements.items():
            value = val[2].GetStringSelection()
            if param == 'random':
                self.action[param] = float(value)
            else:
                try:
                    self.action[param] = int(value)
                except ValueError:
                    self.action[param] = str(value)

        for par, items in self.changes.items():
            value = int(items[2].GetValue())
            self.action['changes'][par] = value
        self.EndModal(True)


class CardPage(wx.Dialog):
    def __init__(self, card):
        self.card = card
        wx.Dialog.__init__(
            self, None, -1, 'Manage Card Details', size=(664, 468))
        self.scroll_panel = scrolled.ScrolledPanel(
            self, -1, size=(1300, 670))

        self.sub_elements = {}
        for param, value in card.items():
            if param not in ('actions'):
                # Create the sizer, label and textcntrl
                this = []
                this.append(wx.BoxSizer(wx.HORIZONTAL))
                this.append(wx.StaticText(self.scroll_panel, -1, param))

                try:
                    value = str(value)
                except ValueError:
                    pass

                this.append(wx.TextCtrl(
                    self.scroll_panel, -1, value, size=(100, 20)))
                # put them in order, add spacer and add to main sizer
                this[0].Add(this[1])
                this[0].AddSpacer(10)
                this[0].Add(this[2])
                # Add to sub_element dictionary
                self.sub_elements[param] = this

        self.action_sizer = wx.BoxSizer(wx.VERTICAL)

        self.add_btn = wx.Button(self.scroll_panel, -1, 'Add Action')
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add)

        self.exit_btn = wx.Button(self.scroll_panel, -1, 'Exit and Save')
        self.exit_btn.Bind(wx.EVT_BUTTON, self.on_exit)

        self.init_layout()

    def init_layout(self):
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_sizer.Add(self.add_btn)
        btn_sizer.Add(self.exit_btn)

        for param in self.sub_elements.values():
            main_sizer.Add(param[0])

        main_sizer.Add(self.action_sizer)
        main_sizer.Add(btn_sizer)

        self.scroll_panel.SetSizer(main_sizer)
        top_sizer.Add(self.scroll_panel)
        self.SetSizer(top_sizer)

        self.scroll_panel.SetupScrolling(True, True)
        self.Layout()

        self.update_actions()

    def update_actions(self):
        # Create button for each action
        self.action_sizer.Clear(True)

        self.displayed_actions = {}

        for a_id in range(len(self.card['actions'])):
            self.displayed_actions[a_id] = wx.Button(
                self.scroll_panel, -1, str(self.card['actions'][a_id]),
                name=str(a_id))
            self.displayed_actions[a_id].Bind(wx.EVT_BUTTON,
                                              self.change_action)
            self.action_sizer.Add(self.displayed_actions[a_id])
            self.action_sizer.AddSpacer(10)

        self.scroll_panel.FitInside()

    def change_action(self, evt):
        name = int(evt.GetEventObject().GetName())
        action = self.card['actions'][name]
        dlg = ActionDetail(action)
        if dlg.ShowModal():
            self.card['actions'][name] = dlg.action

    def on_add(self, evt):
        default_change = {'type': 'change', 'target': 'self',
                          'random': 0, 'changes': {}, 'num_units': 0, 'level': 'id'}
        default_new = {'type': 'new', 'level': 'buildings',
                       'parameters': 0, 'target': 'own'}
        dlg = wx.SingleChoiceDialog(
            self, 'Which action type?', 'Choose Action Type', choices=['change', 'new'])
        if dlg.ShowModal():
            choice = dlg.GetStringSelection()
            if choice == 'new':
                self.card['actions'].append(default_new)
            elif choice == 'change':
                self.card['actions'].append(default_change)

            self.update_actions()

    def on_exit(self, evt):
        self.card['title'] = self.sub_elements['title'][2].GetValue()
        self.card['description'] = self.sub_elements[
            'description'][2].GetValue()
        self.card['num_cards'] = int(self.sub_elements['num_cards']
                                     [2].GetValue())

        self.EndModal(True)


class Sectors(wx.Dialog):
    def __init__(self, sectors):
        self.sectors = sectors
        wx.Dialog.__init__(
            self, None, -1, 'Sector Weight / Importance', size=(664, 468))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sector_elements = {}

        self.sector_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_panel = scrolled.ScrolledPanel(self, -1, size=(300, 350))
        self.scroll_panel.SetSizer(self.sector_sizer)
        self.scroll_panel.SetupScrolling(False, True)

        self.main_sizer.Add(self.scroll_panel)
        self.main_sizer.AddSpacer(20)

        new_btn = wx.Button(self, -1, 'New Sector(s)')
        self.main_sizer.Add(new_btn)
        new_btn.Bind(wx.EVT_BUTTON, self.on_new_sector)

        self.main_sizer.AddSpacer(10)

        exit_btn = wx.Button(self, -1, 'Save and Exit')
        self.main_sizer.Add(exit_btn)
        exit_btn.Bind(wx.EVT_BUTTON, self.on_exit)

        self.SetSizer(self.main_sizer)

        self.update_content()
        self.Layout()

    def update_content(self):
        self.sector_sizer.Clear(True)
        self.sector_elements = {}

        # display all the sectors ordered by key
        for sector in sorted(self.sectors.keys()):
            try:
                weight = self.sectors[sector]['weight']
                victory = self.sectors[sector]['victory']
            except TypeError:
                weight = 1
                victory = 0
            
            # Create the sizer, label and textcntrl
            this = []
            this.append(wx.BoxSizer(wx.HORIZONTAL))
            this.append(wx.StaticText(self.scroll_panel, -1, str(sector)))
            this.append(wx.TextCtrl(
                self.scroll_panel, -1, str(weight), size=(40, 20)))
            this.append(wx.TextCtrl(
                self.scroll_panel, -1, str(victory), size=(40, 20)))
            this.append(wx.Button(
                self.scroll_panel, -1, 'Remove Sector', name=str(sector)))
            this[4].Bind(wx.EVT_BUTTON, self.on_remove)

            # put them in order, add spacer and add to main sizer
            this[0].Add(this[1])
            this[0].AddSpacer(10)
            this[0].Add(this[2])
            this[0].AddSpacer(10)
            this[0].Add(this[3])
            this[0].AddSpacer(10)
            this[0].Add(this[4])
            self.sector_sizer.Add(this[0])
            # Add to sub_element dictionary
            self.sector_elements[sector] = this

        self.scroll_panel.FitInside()

    def on_remove(self, evt):
        sector = int(evt.GetEventObject().GetName())
        del self.sectors[sector]

        self.update_content()

    def on_new_sector(self, evt):
        dlg = wx.TextEntryDialog(
            self, 'Enter new sector number or comma separated numbers (no spaces).',
            'Number of the new sector(s)?')

        if dlg.ShowModal() == wx.ID_OK:
            val = dlg.GetValue()
            try:
                sectors = [int(val)]
            except ValueError:
                sectors = [int(v) for v in val.split(',')]

            for sector in sectors:
                self.sectors[sector] = {'weight': 1, 'victory': 0}

            self.update_content()

    def on_exit(self, evt):
        for sector, elements in self.sector_elements.items():
            weight = float(elements[2].GetValue())
            victory = int(elements[3].GetValue())
            self.sectors[sector] = {'weight': weight, 'victory': victory}

        self.EndModal(True)


class EngineParameters(wx.Dialog):
    def __init__(self, engine_parameters):
        self.engine_parameters = engine_parameters
        wx.Dialog.__init__(
            self, None, -1, 'Engine Parameters', size=(664, 468))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sub_elements = {}
        self.main_sizer.AddSpacer(50)

        param_order = ['start_account', 'constant_per_tick', 'per_sector_per_tick', 'sector_takeover',
            'take_over_factor', 'max_victory_diff', 'delay_damage', 
            'protection_effect', 'protection_in', 'protection_out', 'extra_shoot_dist', 'tick_duration'
            ]

        for param in param_order:
            value = engine_parameters[param]
            if param not in ('all_sectors'):
                # Create the sizer, label and textcntrl
                this = []
                this.append(wx.BoxSizer(wx.HORIZONTAL))
                this.append(wx.StaticText(self, -1, param))
                this.append(
                    wx.TextCtrl(self, -1, str(value), size=(100, 20)))
                # put them in order, add spacer and add to main sizer
                this[0].Add(this[1])
                this[0].AddSpacer(10)
                this[0].Add(this[2])
                self.main_sizer.Add(this[0])
                # Add to sub_element dictionary
                self.sub_elements[param] = this

        self.main_sizer.AddSpacer(25)
        exit_btn = wx.Button(self, -1, 'Save and Exit')
        self.main_sizer.Add(exit_btn)
        exit_btn.Bind(wx.EVT_BUTTON, self.update_values)

        self.SetSizer(self.main_sizer)
        self.Layout()

    def update_values(self, evt):
        for param in self.sub_elements.keys():
            value = self.sub_elements[param][2].GetValue()
            try:
                value = float(value)
            except ValueError:
                pass

            self.engine_parameters[param] = value

        self.EndModal(True)


class DetailPage(wx.Dialog):
    def __init__(self, obj):
        wx.Dialog.__init__(self, None, -1, 'Details for ' + obj[
                           'basic_parameters']['name'], size=(1200, 700))

        self.obj = obj
        self.current_selection = False
        self.is_unit_action = False

        self.detail_ui = {}

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        header = 'Details for ' + obj['basic_parameters']['name'] + \
            ';   Actions;   Upgrade: time;   Upgrade: damage'
        self.main_sizer.Add(wx.StaticText(self, -1, header))
        self.main_sizer.AddSpacer(25)

        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sub_elements = {}

        order = [
            'name', 'price', 'unit_type', 'max_life', 'life', 'max_shield', 'shield', 'capacity', 'enter', 'transports',
            'shop_units', 'shop_transporter', 'delay_in', 'delay_out', 'attack_min', 'attack_max',
            'num_enemies', 'shield_factor', 'shoot_dist', 'delay_shoot', 'walk_dist', 'delay_walk', 'elite']

        for param in order:
            try:
                value = obj['basic_parameters'][param]
                if param not in ('id', 'actions'):
                    if param in ('shop_units', 'shop_transporter'):
                        value = [str(v) for v in value]
                        value = ','.join(value)
                    # Create the sizer, label and textcntrl
                    this = []
                    this.append(wx.BoxSizer(wx.HORIZONTAL))
                    this.append(wx.StaticText(self, -1, param, size=(80, 20)))
                    if param not in ('unit_type', 'enter', 'transports'):
                        this.append(wx.TextCtrl(
                            self, -1, str(value), size=(100, 20)))
                    else:
                        this.append(wx.ComboBox(self, size=(
                            100, 20), choices=['soldier', 'vehicle']))
                        this[2].SetStringSelection(value)

                    # put them in order, add spacer and add to main sizer
                    this[0].Add(this[1])
                    this[0].AddSpacer(10)
                    this[0].Add(this[2])
                    self.left_sizer.Add(this[0])
                    # Add to sub_element dictionary
                    self.sub_elements[param] = this

            except KeyError:
                if param == 'max_shield':
                    self.obj['basic_parameters']['max_shield'] = 0
                pass

        self.action_tree = wx.TreeCtrl(self, -1, size=(300, 350))
        self.Bind(
            wx.EVT_TREE_SEL_CHANGED, self.on_action_change, self.action_tree)

        self.upgrade_time_tree = wx.TreeCtrl(self, -1, size=(300, 350))
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_time_change,
                  self.upgrade_time_tree)

        self.upgrade_damage_tree = wx.TreeCtrl(self, -1, size=(300, 350))
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_damage_change,
                  self.upgrade_damage_tree)

        self.top_sizer.AddSpacer(15)
        self.top_sizer.Add(self.left_sizer)
        self.top_sizer.AddSpacer(15)
        self.top_sizer.Add(self.action_tree)
        self.top_sizer.AddSpacer(15)
        self.top_sizer.Add(self.upgrade_time_tree)
        self.top_sizer.AddSpacer(15)
        self.top_sizer.Add(self.upgrade_damage_tree)

        self.name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.name_ctrl = wx.TextCtrl(self, -1, '', size=(200, 25))
        self.name_label = wx.StaticText(self, -1, 'Unit Action Name:')
        self.name_sizer.Add(self.name_label)
        self.name_sizer.AddSpacer(10)
        self.name_sizer.Add(self.name_ctrl)

        self.main_sizer.Add(self.top_sizer)
        self.main_sizer.AddSpacer(8)
        self.main_sizer.Add(self.name_sizer)
        self.main_sizer.AddSpacer(8)

        self.detail_panel = scrolled.ScrolledPanel(self, -1, size=(700, 100))
        self.detail_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detail_panel.SetSizer(self.detail_sizer)
        self.detail_panel.SetupScrolling(True, True)

        self.main_sizer.Add(self.detail_panel)
        self.main_sizer.AddSpacer(8)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        exit_btn = wx.Button(self, -1, 'Exit & Save')
        exit_btn.Bind(wx.EVT_BUTTON, self.save_exit)
        btn_sizer.Add(exit_btn)

        update_btn = wx.Button(self, -1, 'Update Details')
        update_btn.Bind(wx.EVT_BUTTON, self.update_details)
        btn_sizer.Add(update_btn)

        btn_sizer.AddSpacer(20)

        self.remove_btn = wx.Button(self, -1, 'Remove!')
        self.remove_btn.Bind(wx.EVT_BUTTON, self.remove_current)
        btn_sizer.Add(self.remove_btn)

        btn_sizer.AddSpacer(20)

        self.add_parameter_btn = wx.Button(self, -1, 'Add Parameter')
        self.add_parameter_btn.Bind(wx.EVT_BUTTON, self.add_parameter)
        btn_sizer.Add(self.add_parameter_btn)

        self.add_unit_action_btn = wx.Button(self, -1, 'Add Unit Action')
        self.add_unit_action_btn.Bind(wx.EVT_BUTTON, self.add_unit_action)
        btn_sizer.Add(self.add_unit_action_btn)

        self.add_time_dependent_action_btn = wx.Button(self, -1, 'Add Time Dependent Action')
        self.add_time_dependent_action_btn.Bind(wx.EVT_BUTTON, self.add_time_dependent_action)
        btn_sizer.Add(self.add_time_dependent_action_btn)

        self.add_tick_btn = wx.Button(self, -1, 'Add action at tick/damage')
        self.add_tick_btn.Bind(wx.EVT_BUTTON, self.add_tick)
        btn_sizer.Add(self.add_tick_btn)

        self.add_sub_change_btn = wx.Button(self, -1, 'Add Sub Change')
        self.add_sub_player = wx.Button(self, -1, 'Add Sub Player')
        self.add_sub_new = wx.Button(self, -1, 'Add Sub New Something')

        self.add_sub_change_btn.Bind(wx.EVT_BUTTON, self.add_sub_action_change)
        self.add_sub_player.Bind(wx.EVT_BUTTON, self.add_sub_action_player)
        self.add_sub_new.Bind(wx.EVT_BUTTON, self.add_sub_action_new)

        btn_sizer.AddSpacer(20)
        btn_sizer.Add(self.add_sub_change_btn)
        btn_sizer.Add(self.add_sub_player)
        btn_sizer.Add(self.add_sub_new)

        self.add_sub_change_tick = wx.Button(self, -1, 'Add Sub Change')
        self.add_sub_player_tick = wx.Button(self, -1, 'Add Sub Player')
        self.add_sub_new_tick = wx.Button(self, -1, 'Add Sub New Something')

        self.add_sub_change_tick.Bind(
            wx.EVT_BUTTON, self.add_sub_action_change_tick)
        self.add_sub_player_tick.Bind(
            wx.EVT_BUTTON, self.add_sub_action_player_tick)
        self.add_sub_new_tick.Bind(wx.EVT_BUTTON, self.add_sub_action_new_tick)

        btn_sizer.AddSpacer(20)
        btn_sizer.Add(self.add_sub_change_tick)
        btn_sizer.Add(self.add_sub_player_tick)
        btn_sizer.Add(self.add_sub_new_tick)

        btn_sizer.AddSpacer(20)
        self.change_btn = wx.Button(self, -1, 'Change Tick/Damage')
        self.change_btn.Bind(wx.EVT_BUTTON, self.change_tick)
        btn_sizer.Add(self.change_btn)

        btn_sizer.AddSpacer(20)

        self.main_sizer.Add(btn_sizer)

        self.SetSizer(self.main_sizer)
        self.update_all()

        self.Layout()

    def on_damage_change(self, evt):
        item_sel = evt.GetItem()
        selection = False

        self.is_unit_action = False

        if not item_sel:
            return

        found = False

        complete_adress = self.action_tree.GetItemPyData(item_sel)
        self.last_item = complete_adress[len(complete_adress) - 1]
        if type(self.last_item) != int:
            if len(self.last_item) > 6:
                if self.last_item[:6] == 'ticks_':
                    found = True
                    selection = 'ticks'
                    self.last_item = int(self.last_item[6:])

            if not found:
                if len(self.last_item) > 10:
                    if self.last_item[:10] == 'parameter_':
                        selection = 'parameter'
                        self.last_item = self.last_item[10:]
                    else:
                        selection = 'unit_action'
                        self.is_unit_action = True
                else:
                    selection = 'unit_action'
                    self.is_unit_action = True
        else:
            selection = 'sub_action'

        if complete_adress == tuple(['root']):
            selection = 'root_tick'

        # get the requested field
        def get_action(adress):
            cur_action = self.obj['elite_parameters']['damage']
            last = len(adress) - 1
            for item_id in range(len(adress)):
                item = adress[item_id]
                # or if it is a sub action (integer)
                try:
                    item = int(item)
                    if item_id != last:
                        cur_action = cur_action[item]['changes']
                    else:
                        return cur_action

                # check if item is a unit action (string)
                # or if it is a parameter (string starting with parameter_)
                except ValueError:
                    found = False
                    if len(item) > 6:
                        if item[:6] == 'ticks_':
                            found = True
                            num_ticks = int(item[6:])
                            if item_id != last:
                                cur_action = cur_action[num_ticks]
                            else:
                                return cur_action

                    if len(item) > 10 and not found:
                        if item[:10] == 'parameter_':
                            item = item[10:]
                            return cur_action

                    # A unit action
                    # Rerout to sub actions
                    if not found:
                        if item_id != last:
                            cur_action = cur_action['actions'][item]['actions']
                        else:
                            return cur_action['actions']

        if len(complete_adress) > 1:
            complete_adress = complete_adress[1:]
            self.current_item = get_action(complete_adress)
        else:
            self.current_item = self.obj['elite_parameters']['damage']

        self.detail_sizer.Clear()

        for param in self.detail_ui.keys():
            self.detail_ui[param][1].Destroy()
            self.detail_ui[param][2].Destroy()

        self.detail_ui = {}

        if self.current_item is None:
            self.detail_panel.FitInside()
            return

        self.update_buttons(selection)

    def on_time_change(self, evt):
        item_sel = evt.GetItem()
        selection = False

        self.is_unit_action = False

        if not item_sel:
            return

        found = False

        complete_adress = self.action_tree.GetItemPyData(item_sel)
        self.last_item = complete_adress[len(complete_adress) - 1]
        if type(self.last_item) != int:
            if len(self.last_item) > 6:
                if self.last_item[:6] == 'ticks_':
                    found = True
                    selection = 'ticks'
                    self.last_item = int(self.last_item[6:])

            if not found:
                if len(self.last_item) > 10:
                    if self.last_item[:10] == 'parameter_':
                        selection = 'parameter'
                        self.last_item = self.last_item[10:]
                    else:
                        selection = 'unit_action'
                        self.is_unit_action = True
                else:
                    selection = 'unit_action'
                    self.is_unit_action = True
        else:
            selection = 'sub_action'

        if complete_adress == tuple(['root']):
            selection = 'root_tick'

        # get the requested field
        def get_action(adress):
            cur_action = self.obj['elite_parameters']['ticks']
            last = len(adress) - 1
            for item_id in range(len(adress)):
                item = adress[item_id]
                # or if it is a sub action (integer)
                try:
                    item = int(item)
                    if item_id != last:
                        cur_action = cur_action[item]['changes']
                    else:
                        return cur_action

                # check if item is a unit action (string)
                # or if it is a parameter (string starting with parameter_)
                except ValueError:
                    found = False
                    if len(item) > 6:
                        if item[:6] == 'ticks_':
                            found = True
                            num_ticks = int(item[6:])
                            if item_id != last:
                                cur_action = cur_action[num_ticks]
                            else:
                                return cur_action

                    if len(item) > 10 and not found:
                        if item[:10] == 'parameter_':
                            item = item[10:]
                            return cur_action

                    # A unit action
                    # Rerout to sub actions
                    if not found:
                        if item_id != last:
                            cur_action = cur_action['actions'][item]['actions']
                        else:
                            return cur_action['actions']

        if len(complete_adress) > 1:
            complete_adress = complete_adress[1:]
            self.current_item = get_action(complete_adress)
        else:
            self.current_item = self.obj['elite_parameters']['ticks']

        self.detail_sizer.Clear()

        for param in self.detail_ui.keys():
            self.detail_ui[param][1].Destroy()
            self.detail_ui[param][2].Destroy()

        self.detail_ui = {}

        if self.current_item is None:
            self.detail_panel.FitInside()
            return

        self.update_buttons(selection)

    def update_buttons(self, selection):
        self.sel_root = False

        if selection in ('unit_action', 'sub_action', 'time_dependent_action'):
            to_display = self.current_item[self.last_item]

        #elif selection == 'time_dependent_action':
        #    to_display = self.current_item['time_dependent_actions'][self.last_item]

        if selection in ('time_dependent_action', 'unit_action'):
            self.name_ctrl.SetLabel(str(self.last_item))

        elif selection == 'ticks':
            to_display = {}

        elif selection == 'parameter':
            to_display = {self.last_item: self.current_item[self.last_item]}

        elif selection in ('root', 'root_tick'):
            self.last_item = -1
            to_display = {}
            self.sel_root = True

        for param, value in to_display.items():
            if param not in ('actions', 'changes'):
                if param in ('shop_units', 'shop_transporter', 'parameters'):
                    if type(value) not in (int, float):
                        value = [str(v) for v in value]
                        value = ','.join(value)
                    else:
                        value = str(value)

                this = []
                this.append(wx.BoxSizer(wx.VERTICAL))
                this.append(wx.StaticText(self.detail_panel, -1, param))
                if param == 'target':
                    this.append(wx.ComboBox(self.detail_panel, size=(
                        100, 20), choices=['self', 'own', 'enemy']))
                    this[2].SetStringSelection(value)
                elif param == 'type':
                    this.append(wx.ComboBox(self.detail_panel,
                                size=(100, 20), choices=['change', 'new']))
                    this[2].SetStringSelection(value)
                elif param == 'level':
                    this.append(wx.ComboBox(self.detail_panel, size=(
                        100, 20), choices=['id', 'groups', 'buildings', 'transporter', 'player']))
                    this[2].SetStringSelection(value)
                elif param == 'category':
                    this.append(wx.ComboBox(self.detail_panel, size=(
                        100, 20), choices=['upgrade', 'shop', 'equipment', 'standard']))
                    this[2].SetStringSelection(value)
                else:
                    this.append(wx.TextCtrl(
                        self.detail_panel, -1, str(value), size=(100, 20)))
                # put them in order, add spacer and add to main sizer
                this[0].Add(this[1])
                this[0].AddSpacer(10)
                this[0].Add(this[2])
                self.detail_sizer.Add(this[0])
                # Add to sub_element dictionary
                self.detail_ui[param] = this

        if selection not in ('unit_action', 'time_dependent_action'):
            self.name_ctrl.Hide()
            self.name_label.Hide()
        else:
            self.name_ctrl.Show()
            self.name_label.Show()

        if selection == 'parameter':
            self.add_parameter_btn.Hide()
            self.add_unit_action_btn.Hide()
            self.add_time_dependent_action_btn.Hide()
            self.add_sub_change_btn.Hide()
            self.add_sub_player.Hide()
            self.add_sub_new.Hide()
            self.add_tick_btn.Hide()
            self.add_sub_player_tick.Hide()
            self.add_sub_new_tick.Hide()
            self.add_sub_change_tick.Hide()
            self.change_btn.Hide()

        elif selection in ('unit_action', 'time_dependent_action'):
            self.add_parameter_btn.Hide()
            self.add_unit_action_btn.Hide()
            self.add_time_dependent_action_btn.Hide()
            self.add_sub_change_btn.Show()
            self.add_sub_player.Show()
            self.add_sub_new.Show()
            self.add_tick_btn.Hide()
            self.add_sub_player_tick.Hide()
            self.add_sub_new_tick.Hide()
            self.add_sub_change_tick.Hide()
            self.change_btn.Hide()

        elif selection in ('ticks'):
            self.add_parameter_btn.Hide()
            self.add_unit_action_btn.Hide()
            self.add_time_dependent_action_btn.Hide()
            self.add_sub_change_btn.Hide()
            self.add_sub_player.Hide()
            self.add_sub_new.Hide()
            self.add_tick_btn.Hide()
            self.add_sub_player_tick.Show()
            self.add_sub_new_tick.Show()
            self.add_sub_change_tick.Show()
            self.change_btn.Show()

        elif selection == 'sub_action':
            self.add_parameter_btn.Show()
            self.add_unit_action_btn.Show()
            self.add_time_dependent_action_btn.Show()
            self.add_sub_change_btn.Hide()
            self.add_sub_player.Hide()
            self.add_sub_new.Hide()
            self.add_tick_btn.Hide()
            self.add_sub_player_tick.Hide()
            self.add_sub_new_tick.Hide()
            self.add_sub_change_tick.Hide()
            self.change_btn.Hide()

        elif selection == 'root':
            self.add_parameter_btn.Hide()
            self.add_unit_action_btn.Show()
            self.add_time_dependent_action_btn.Hide()
            self.add_sub_change_btn.Hide()
            self.add_sub_player.Hide()
            self.add_sub_new.Hide()
            self.add_tick_btn.Hide()
            self.add_sub_player_tick.Hide()
            self.add_sub_new_tick.Hide()
            self.add_sub_change_tick.Hide()
            self.change_btn.Hide()

        elif selection == 'root_tick':
            self.add_parameter_btn.Hide()
            self.add_unit_action_btn.Hide()
            self.add_time_dependent_action_btn.Hide()
            self.add_sub_change_btn.Hide()
            self.add_sub_player.Hide()
            self.add_sub_new.Hide()
            self.add_tick_btn.Show()
            self.add_sub_player_tick.Hide()
            self.add_sub_new_tick.Hide()
            self.add_sub_change_tick.Hide()
            self.change_btn.Hide()

        self.detail_panel.FitInside()
        self.Layout()

    def on_action_change(self, evt):
        item_sel = evt.GetItem()
        selection = False

        self.is_unit_action = False

        if not item_sel:
            return

        complete_adress = self.action_tree.GetItemPyData(item_sel)
        self.last_item = complete_adress[len(complete_adress) - 1]
        if type(self.last_item) != int:
            if len(self.last_item) > 10:
                if self.last_item[:10] == 'parameter_':
                    selection = 'parameter'
                    self.last_item = self.last_item[10:]
                else:
                    selection = 'unit_action'
                    self.is_unit_action = True
            else:
                selection = 'unit_action'
                self.is_unit_action = True
        else:
            if type(self.current_item) != list:
                selection = 'sub_action'
            else:
                selection = 'time_dependent_action'
                self.is_unit_action = True

        if complete_adress == tuple(['root']):
            selection = 'root'

        print selection

        # get the requested field
        def get_action(adress):
            cur_action = self.obj['basic_parameters']
            last = len(adress) - 1
            for item_id in range(len(adress)):
                item = adress[item_id]

                # or if it is a sub action or time_dependent(integer)
                try:
                    item = int(item)
                    if type(adress[item_id-1]) != int or type(cur_action) == list:
                        #Sub action
                        if item_id != last:
                                cur_action = cur_action[item]['changes']
                        else:
                            return cur_action

                    else:
                        # time_dependent
                        if item_id != last:
                            cur_action = cur_action['time_dependent_actions'][item]['actions']
                        else:
                            if type(cur_action) == dict:
                                return cur_action['time_dependent_actions']
                            else:
                                return cur_action

                # check if item is a unit action (string)
                # or if it is a parameter (string starting with parameter_)
                except ValueError:
                    if len(item) > 10:
                        if item[:10] == 'parameter_':
                            item = item[10:]
                            return cur_action

                    # A unit action
                    # Rerout to sub actions
                    if item_id != last:
                        cur_action = cur_action['actions'][item]['actions']
                    else:
                        return cur_action['actions']

        if len(complete_adress) > 1:
            complete_adress = complete_adress[1:]
            self.current_item = get_action(complete_adress)
        else:
            self.current_item = self.obj['basic_parameters']

        self.detail_sizer.Clear()

        for param in self.detail_ui.keys():
            self.detail_ui[param][1].Destroy()
            self.detail_ui[param][2].Destroy()

        self.detail_ui = {}

        if self.current_item is None:
            self.detail_panel.FitInside()
            return

        self.update_buttons(selection)

    def remove_current(self, evt):
        if not self.sel_root:
            del self.current_item[self.last_item]
            self.update_all()
        else:
            self.EndModal(False)

    def update_all(self):
        self.update_actions()
        self.update_time_upgrades()
        self.update_damage_upgrades()

    def change_tick(self, evt):
        dlg = wx.TextEntryDialog(
            self, 'New tick/damage value?',
            'Eh??')

        if dlg.ShowModal() == wx.ID_OK:
            new_tick = int(dlg.GetValue())

            self.current_item[new_tick] = self.current_item[self.last_item]
            del self.current_item[self.last_item]
            self.update_all()

    def add_tick(self, evt):
        dlg = wx.TextEntryDialog(
            self, 'At which tick/damage value?',
            'Eh??')

        if dlg.ShowModal() == wx.ID_OK:
            new_param = int(dlg.GetValue())
            self.current_item[new_param] = []
            self.update_all()

    def add_parameter(self, evt):
        dlg = wx.TextEntryDialog(
            self, 'Which parameter do you want to add?',
            'Eh??')

        if dlg.ShowModal() == wx.ID_OK:
            new_param = dlg.GetValue()
            if new_param in ('shop_transporter', 'shop_units'):
                new_val = []
            elif new_param in ('name'):
                new_val = ''
            elif new_param in ('enter', 'transports', 'unit_type'):
                new_val = 'soldier'
            elif new_param in ('elite'):
                new_val = 1
            else:
                new_val = 0

            self.current_item[self.last_item]['changes'][new_param] = new_val
            self.update_all()

    def add_unit_action(self, evt):
        dlg = wx.TextEntryDialog(
            self, 'What is the name of the new unit action?',
            'Eh??')

        default_action = {'price': 0, 'delay': 0, 'num_uses': -1,
                          'category': 'upgrade', 'actions': []}

        if dlg.ShowModal() == wx.ID_OK:
            new_param = dlg.GetValue()
            if self.last_item != -1:
                if 'actions' not in self.current_item[self.last_item]['changes'].keys():
                    self.current_item[self.last_item][
                        'changes']['actions'] = {}

                self.current_item[self.last_item][
                    'changes']['actions'][new_param] = default_action

            else:
                self.current_item['actions'][new_param] = default_action

            self.update_all()

    def add_time_dependent_action(self, evt):
        dlg = wx.TextEntryDialog(
            self, 'When does the action come up (now + n ticks)?',
            'Eh??')

        default_action = {'price': 0, 'delay': 0, 'num_uses': -1,
                          'category': 'upgrade', 'actions': []}

        if dlg.ShowModal() == wx.ID_OK:
            new_param = int(dlg.GetValue())
            if self.last_item != -1:
                if 'time_dependent_actions' not in self.current_item[self.last_item]['changes'].keys():
                    self.current_item[self.last_item][
                        'changes']['time_dependent_actions'] = {}

                self.current_item[self.last_item][
                    'changes']['time_dependent_actions'][new_param] = default_action

            else:
                print 'triggered'
                self.current_item['time_dependent_actions'][new_param] = default_action

            self.update_all()

    def add_sub_action_change(self, evt):

        default_action = {'type': 'change', 'target': 'self',
                          'random': 0, 'changes': {}, 'num_units': 0, 'level': 'id'}

        self.current_item[self.last_item]['actions'].append(default_action)
        self.update_all()

    def add_sub_action_player(self, evt):
        default_action = {'type': 'change', 'target': 'enemy',
                          'level': 'player', 'random': 1, 'changes': {}}

        self.current_item[self.last_item]['actions'].append(default_action)
        self.update_all()

    def add_sub_action_new(self, evt):
        default_action = {'type': 'new', 'level': 'buildings',
                          'parameters': 0, 'target': 'own'}

        self.current_item[self.last_item]['actions'].append(default_action)
        self.update_all()

    def add_sub_action_change_tick(self, evt):
        default_action = {'type': 'change', 'target': 'self',
                          'random': 0, 'changes': {}, 'num_units': 0, 'level': 'id'}

        self.current_item[self.last_item].append(default_action)
        self.update_all()

    def add_sub_action_player_tick(self, evt):
        default_action = {'type': 'change', 'target': 'enemy',
                          'level': 'player', 'random': 1, 'changes': {}}
        self.current_item[self.last_item].append(default_action)
        self.update_all()

    def add_sub_action_new_tick(self, evt):
        default_action = {'type': 'new', 'level': 'buildings',
                          'parameters': 0, 'target': 'own'}
        self.current_item[self.last_item].append(default_action)
        self.update_all()

    def update_details(self, evt):
        try:
            new_level = self.detail_ui['level'][2].GetValue()
        except KeyError:
            new_level = False

        for param in self.detail_ui.keys():
            value = self.detail_ui[param][2].GetValue()
            if param in ('shop_units', 'shop_transporter'):
                value = value.split(',')
                value = [int(n) for n in value]

            elif param == 'parameters':
                if new_level == 'groups':
                    value = value.split(',')
                    value = [int(n) for n in value]
                else:
                    value = int(float(value))

            elif param in ['random', 'shield_factor']:
                value = float(value)

            else:
                try:
                    value = int(float(value))
                except ValueError:
                    pass

            try:
                self.current_item[self.last_item][param] = value
            except TypeError:
                self.current_item[self.last_item] = value

        cur_name = self.name_ctrl.GetValue()

        if self.is_unit_action:
            if cur_name != self.last_item and type(self.last_item) != int:  
                self.current_item[cur_name] = self.current_item[self.last_item]
                del self.current_item[self.last_item]

            elif int(cur_name) != self.last_item and type(self.last_item) == int:  
                self.current_item[int(cur_name)] = self.current_item[self.last_item]
                del self.current_item[self.last_item]


        self.update_all()

    def update_actions(self):

        self.action_tree.DeleteAllItems()
        self.actions = {}

        def add_item(name, adress, previous_adress):
            self.actions[adress] = self.action_tree.AppendItem(
                self.actions[previous_adress], name)
            self.action_tree.SetPyData(self.actions[adress], adress)

        def add_nested_unit_actions(name, action, initial_adress, unit_action = True):
            '''Recursively add new items to the root'''
            this_adress = tuple(list(initial_adress) + [name])
            if unit_action:
                add_item('Unit Action: ' + name + ': ' + str(
                    action['price']) + '$', this_adress, initial_adress)
            else:
                add_item('Time Dependent Action: (' + str(name) + ' ticks)', this_adress, initial_adress)

            for act_id in range(len(action['actions'])):
                act = action['actions'][act_id]
                sub_adress = tuple(list(this_adress) + [act_id])
                add_item(
                    'Sub Action: ' + act['target'], sub_adress, this_adress)
                try:
                    changes = act['changes']
                except KeyError:
                    changes = {}

                for param, change in changes.items():
                        if param == 'actions':
                            for name, action in change.items():
                                add_nested_unit_actions(
                                    name, action, sub_adress)

                        elif param == 'time_dependent_actions':
                            for tick, action in change.items():
                                add_nested_unit_actions(tick, action, sub_adress, False)
                        else:
                            item_adress = tuple(
                                list(sub_adress) + ['parameter_' + param])
                            add_item('Parameter: ' + param +
                                     '  ' + str(change), item_adress, sub_adress)

        root_adress = tuple(['root'])
        self.actions[root_adress] = self.action_tree.AddRoot('Root (Unit)')
        self.action_tree.SetPyData(self.actions[root_adress], root_adress)
        self.action_tree.SelectItem(self.actions[root_adress])

        for name, action in self.obj['basic_parameters']['actions'].items():
            add_nested_unit_actions(name, action, root_adress)

        self.action_tree.ExpandAll()

    def update_time_upgrades(self):

        self.upgrade_time_tree.DeleteAllItems()
        self.time_upgrades = {}

        def add_item(name, adress, previous_adress):
            self.time_upgrades[adress] = self.action_tree.AppendItem(
                self.time_upgrades[previous_adress], name)
            self.upgrade_time_tree.SetPyData(
                self.time_upgrades[adress], adress)

        def add_nested_sub_actions(act_id, action, initial_adress):
            '''Recursively add new items to the root'''
            this_adress = tuple(list(initial_adress) + [act_id])
            add_item('Sub Action: ' + str(act_id), this_adress, initial_adress)
            try:
                changes = action['changes']
            except KeyError:
                changes = {}

            for param, change in changes.items():
                if param == 'actions':
                    for name, unit_action in change.items():
                        sub_adress = tuple(list(this_adress) + [name])

                        add_item('Unit Action: ' + str(name) + ': ' + str(
                            unit_action['price']) + '$', sub_adress, this_adress)
                        for act_id in range(len(unit_action['actions'])):
                            act = unit_action['actions'][act_id]
                            add_nested_sub_actions(act_id, act, sub_adress)
                else:
                    item_adress = tuple(
                        list(this_adress) + ['parameter_' + param])
                    add_item('Parameter: ' + param +
                             ': ' + str(change), item_adress, this_adress)

        root_adress = tuple(['root'])
        self.time_upgrades[root_adress] = self.upgrade_time_tree.AddRoot(
            'Root time dependent upgrade')
        self.upgrade_time_tree.SetPyData(
            self.time_upgrades[root_adress], root_adress)
        self.upgrade_time_tree.SelectItem(self.time_upgrades[root_adress])

        for ticks, actions in self.obj['elite_parameters']['ticks'].items():
            tick_adress = tuple(list(root_adress) + ['ticks_' + str(ticks)])
            add_item('After {0} ticks'.format(ticks), tick_adress, root_adress)
            for act_id in range(len(actions)):
                action = actions[act_id]
                add_nested_sub_actions(act_id, action, tick_adress)

        self.upgrade_time_tree.ExpandAll()

    def update_damage_upgrades(self):

        self.upgrade_damage_tree.DeleteAllItems()
        self.damage_upgrades = {}

        def add_item(name, adress, previous_adress):
            self.damage_upgrades[adress] = self.action_tree.AppendItem(
                self.damage_upgrades[previous_adress], name)
            self.upgrade_damage_tree.SetPyData(
                self.damage_upgrades[adress], adress)

        def add_nested_sub_actions(act_id, action, initial_adress):
            '''Recursively add new items to the root'''
            this_adress = tuple(list(initial_adress) + [act_id])
            add_item('Sub Action: ' + str(act_id), this_adress, initial_adress)
            try:
                changes = action['changes']
            except KeyError:
                changes = {}

            for param, change in changes.items():
                if param == 'actions':
                    for name, unit_action in change.items():
                        sub_adress = tuple(list(this_adress) + [name])

                        add_item('Unit Action: ' + str(name) + ': ' + str(
                            unit_action['price']) + '$', sub_adress, this_adress)
                        for act_id in range(len(unit_action['actions'])):
                            act = unit_action['actions'][act_id]
                            add_nested_sub_actions(act_id, act, sub_adress)
                else:
                    item_adress = tuple(
                        list(this_adress) + ['parameter_' + param])
                    add_item('Parameter: ' + param +
                             ': ' + str(change), item_adress, this_adress)

        root_adress = tuple(['root'])
        self.damage_upgrades[root_adress] = self.upgrade_damage_tree.AddRoot(
            'Root damage dependent upgrade')
        self.upgrade_damage_tree.SetPyData(
            self.damage_upgrades[root_adress], root_adress)
        self.upgrade_damage_tree.SelectItem(self.damage_upgrades[root_adress])

        for ticks, actions in self.obj['elite_parameters']['damage'].items():
            tick_adress = tuple(list(root_adress) + ['ticks_' + str(ticks)])
            add_item(
                'After {0} damage'.format(ticks), tick_adress, root_adress)
            for act_id in range(len(actions)):
                action = actions[act_id]
                add_nested_sub_actions(act_id, action, tick_adress)

        self.upgrade_damage_tree.ExpandAll()

    def save_exit(self, evt):
        for param, content in self.sub_elements.items():
            if param in ('shop_units', 'shop_transporter'):
                value = content[2].GetValue()
                if value == '':
                    value = []
                else:
                    value = value.split(',')
                    value = [int(n) for n in value]

            elif param == 'shield_factor':
                value = content[2].GetValue()
                value = float(value)

            else:
                value = content[2].GetValue()
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = int(float(value))
                    except ValueError:
                        pass

            self.obj['basic_parameters'][param] = value

        self.EndModal(True)


if __name__ == '__main__':
    app = wx.App(
        # redirect=True,filename="helper_crash_log.txt"
    )

    ConfigurationHelper()

    app.MainLoop()
