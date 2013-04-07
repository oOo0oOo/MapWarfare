import wx
import wx.lib.buttons as buttons
import wx.lib.scrolledpanel as scrolled
import wx.lib.agw.pygauge as pg
import action_wizard
from collections import Counter

INITIATE_ACTION = wx.NewEventType()
EVT_INITIATE_ACTION = wx.PyEventBinder(INITIATE_ACTION, 1)


class ActionEvent(wx.PyCommandEvent):

    def __init__(self, evtType, ind, action_type=None,
                 o_id=None, u_id=None, action_name=None):
        wx.PyCommandEvent.__init__(self, evtType, ind)
        # Data associated with an action event
        self.action_type = action_type
        self.o_id = o_id
        self.u_id = u_id
        self.action_name = action_name


class MainFrame(wx.Frame):

    def __init__(self, parent, title, all_graphics, connection):
        wx.Frame.__init__(self, parent, title=title, size=(1366, 768))

        # Define some global fonts and colors
        # Done at this point because wx.Font() requires running wx.App
        global colors
        global fonts
        colors = {}
        fonts = {}

        colors[0] = '#000000'  # Main background (dark dark blue)
        colors[1] = '#139EC7'  # Used as main background for most panels (light blue)
        colors[2] = '#046380'  # Used as background for the summary panel (darker blue)

        font_family = wx.FONTFAMILY_SWISS
        fonts['parameter'] = wx.Font(10, font_family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        fonts['small'] = wx.Font(8, font_family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        fonts['large_number'] = wx.Font(25, font_family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        fonts['title'] = wx.Font(12, font_family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.connection = connection
        self.all_graphics = all_graphics

        self.game_obj = {}
        self.cards = {}
        self.sectors = {}

        self.focused_id = -1

        self.game_parameters = {}
        self.selected_ids = []
        self.enemy_groups = {}

        # create istances of all other
        self.header = Header(self, self.all_graphics, self.connection)
        self.card_panel = CardPanel(self, self.all_graphics)
        self.message_board = MessageBoard(self, 10, self.all_graphics)
        self.icon_panel = IconPanel(self, self.all_graphics)
        self.bottom_panel = BottomPanel(
            self, self.all_graphics, self.connection)

        # icon_panel is dark blue
        self.icon_panel.SetBackgroundColour(colors[2])
        self.message_board.SetBackgroundColour(colors[1])
        self.bottom_panel.SetBackgroundColour(colors[1])
        self.header.SetBackgroundColour(colors[1])
        self.card_panel.SetBackgroundColour(colors[1])

        self.DoLayout()

        self.Maximize()
        self.Layout()

        # Bind handler for all button clicks on items
        self.Bind(wx.EVT_BUTTON, self.icon_selected)

        # Bind handler for action events
        self.Bind(EVT_INITIATE_ACTION, self.initiate_action)

        # Set up keyboard shortcuts (0-9) select number
        shortcuts = []
        ids = {}
        for i in range(10):
            ids[i] = wx.NewId()
            shortcuts.append((wx.ACCEL_NORMAL, ord(str(i)), ids[i]))
            self.Bind(wx.EVT_MENU, lambda evt, i=i:
                      self.on_shortcut(evt, i), id=ids[i])

        # key F triggers fullscreen
        ind = wx.NewId()
        shortcuts.append((wx.ACCEL_NORMAL, ord('F'), ind))
        self.Bind(wx.EVT_MENU, self.on_fullscreen, id=ind)

        # key ESC can be used to end fullscreen
        ind = wx.NewId()
        shortcuts.append((wx.ACCEL_NORMAL, wx.WXK_ESCAPE, ind))
        self.Bind(wx.EVT_MENU, self.end_fullscreen, id=ind)

        accel_tbl = wx.AcceleratorTable(shortcuts)
        self.SetAcceleratorTable(accel_tbl)

    def DoLayout(self):
        self.SetBackgroundColour(colors[0])

        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.upper_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.upper_sizer.Add(self.header, 0, wx.RIGHT, 10)
        self.upper_sizer.Add(self.card_panel, 0, wx.EXPAND)
        self.middle_sizer.Add(self.icon_panel, 0, wx.RIGHT, 10)
        self.middle_sizer.Add(self.message_board, 0, wx.EXPAND)

        self.main_sizer.Add(self.upper_sizer, 0, wx.TOP, 10)
        self.main_sizer.Add(self.middle_sizer, 0, wx.TOP, 10)
        self.main_sizer.Add(self.bottom_panel, 0, wx.TOP, 10)

        self.top_sizer.Add(self.main_sizer, 0, wx.LEFT, 10)

        self.SetSizer(self.top_sizer)

    def on_fullscreen(self, evt):
        self.ShowFullScreen(not self.IsFullScreen(), wx.FULLSCREEN_ALL)

    def end_fullscreen(self, evt):
        if self.IsFullScreen():
            self.ShowFullScreen(False)

    def on_shortcut(self, evt, o_id):
        g_o = self.game_obj
        if o_id in g_o['groups'].keys() + g_o['transporter'].keys() + g_o['buildings'].keys():
            if self.selected_ids != [o_id]:
                self.selected_ids = [o_id]
                self.bottom_panel.update_selection(self.selected_ids)
                self.icon_panel.shortcut_used(o_id)
            else:
                self.selected_ids = []
                self.bottom_panel.update_selection(self.selected_ids)
                self.icon_panel.shortcut_used(-1)

    def initiate_action(self, evt):
        if evt.action_type not in ('move_units', 'rename', 'buy_card', 'play_card'):
            if evt.action_type == 'unit_action':
                ids = [self.focused_id]
            else:
                ids = self.selected_ids

            # Call action wizard
            wiz = action_wizard.ActionWizard(
                evt, ids, self.enemy_groups, self.sectors,
                self.game_obj['groups'], self.game_obj[
                    'transporter'], self.game_obj['buildings'],
                self.cards, self.connection)
        elif evt.action_type == 'move_units':
            selected_groups = {}
            g_keys = self.game_obj['groups'].keys()
            for ind in self.selected_ids:
                if ind in g_keys:
                    group = self.game_obj['groups'][ind]
                    selected_groups[ind] = group

            dlg = MoveUnits(
                self, selected_groups, self.all_graphics, self.connection)
            dlg.ShowModal()

        elif evt.action_type == 'rename':
            dlg = wx.TextEntryDialog(
                None, 'Rename ID', 'Choose a new name for the ID')
            res = dlg.ShowModal()
            if res:
                data = {'action': 'rename_id', 'id':
                        self.selected_ids[0], 'name': dlg.GetValue()}
                self.connection.Send(data)

        elif evt.action_type == 'buy_card':
            choices = self.game_parameters['card_parameters'].keys()
            choices = [str(c) for c in choices]
            dlg = wx.SingleChoiceDialog(
                None, 'Chooces Card Stack', 'How much do you want to pay for the card?',
                choices=choices)
            res = dlg.ShowModal()
            if res:
                data = {'action': 'buy_card', 'amount':
                        int(dlg.GetStringSelection())}
                self.connection.Send(data)

        elif evt.action_type == 'play_card':
            choices = {}
            for ind, card in self.cards.items():
                choices[card['title']] = ind

            ch_disp = choices.keys()
            if len(ch_disp) > 0:
                dlg = wx.SingleChoiceDialog(None, 'Choose Card', 'Which Card?',
                                            choices=ch_disp)
                res = dlg.ShowModal()
                if res:
                    evt.o_id = choices[dlg.GetStringSelection()]
                    wiz = action_wizard.ActionWizard(
                        evt, [], self.enemy_groups, self.sectors,
                        self.game_obj['groups'], self.game_obj[
                            'transporter'], self.game_obj['buildings'],
                        self.cards, self.connection)

    def icon_selected(self, event):
        button = event.GetEventObject()
        ind = int(button.GetName())

        if ind in self.selected_ids:
            self.selected_ids.remove(ind)
            self.bottom_panel.update_selection(self.selected_ids)
        else:
            self.selected_ids.append(ind)
            self.bottom_panel.update_selection(self.selected_ids)
            self.focused_id = ind

    def add_message(self, msg):
        self.message_board.add_message(msg)

    def update_ui(self, data):
        # update groups, transporter and buildings
        groups = data['groups'] or data['groups'] == {}
        transporter = data['transporter'] or data['transporter'] == {}
        buildings = data['buildings'] or data['buildings'] == {}
        cards = data['cards'] or data['cards'] == {}

        # update the icon panel if all data is present
        if groups and transporter and buildings:
            self.game_obj = {'groups': data['groups'],
                             'transporter': data['transporter'],
                             'buildings': data['buildings']}

            self.icon_panel.update_displayed(self.game_obj)
            self.bottom_panel.update_objects(self.game_obj)

        if data['game_parameters']:
            self.game_parameters = data['game_parameters']
            self.bottom_panel.update_game_parameters(self.game_parameters)
            self.header.set_max(self.game_parameters['engine_parameters']['max_victory_diff'])

        if data['enemy_groups'] or data['enemy_groups'] == {}:
            self.enemy_groups = data['enemy_groups']

        if data['sectors']:
            self.sectors = data['sectors']

        if cards:
            self.cards = data['cards']

        if data['status']:
            self.header.update_status(data['status'])

        try:
            self.header.update_play(data['play'])
        except KeyError:
            pass

        try:
            if data['update_selection']:
                self.bottom_panel.update_selection(self.selected_ids)
        except KeyError:
            pass


class CardPanel(wx.Panel):

    def __init__(self, parent, all_graphics):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.all_graphics = all_graphics

        self.buy_card_btn = wx.BitmapButton(
            self, -1, self.all_graphics['action_buy'], style=wx.BORDER_NONE)
        self.play_card_btn = wx.BitmapButton(
            self, -1, self.all_graphics['action_card'], style=wx.BORDER_NONE)

        self.buy_card_btn.SetBackgroundColour(colors[1])
        self.play_card_btn.SetBackgroundColour(colors[1])

        self.buy_card_btn.Bind(wx.EVT_BUTTON, self.on_buy_card)
        self.play_card_btn.Bind(wx.EVT_BUTTON, self.on_play_card)

        self.init_layout()

    def init_layout(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(self.buy_card_btn)
        main_sizer.AddSpacer(5)
        main_sizer.Add(self.play_card_btn)
        self.SetSizer(main_sizer)
        self.Layout()

    def on_play_card(self, evt):
        # create and process ActionEvent (handled in Main Frame)
        new_event = ActionEvent(
            INITIATE_ACTION, self.GetId(), action_type='play_card')
        self.GetEventHandler().ProcessEvent(new_event)

    def on_buy_card(self, evt):
        # create and process ActionEvent (handled in Main Frame)
        new_event = ActionEvent(
            INITIATE_ACTION, self.GetId(), action_type='buy_card')
        self.GetEventHandler().ProcessEvent(new_event)


class Header(wx.Panel):

    def __init__(self, parent, all_graphics, connection):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, size=(1000, -1))
        self.connection = connection
        self.all_graphics = all_graphics
        self.run_ticks = False

        self.SetMinSize((1000, -1))
        params = ['name', 'account', 'sectors']
        self.displayed = {}
        for param in params:
            self.displayed['icon_' + param] = wx.StaticBitmap(
                self, bitmap=self.all_graphics['unknown'])
            self.displayed[param] = wx.StaticText(self, -1, '')
            self.displayed[param].SetFont(fonts['title'])

        # Display victory difference
        self.victory = pg.PyGauge(self, -1, size=(200, 20), style=wx.GA_HORIZONTAL)
        self.victory.SetBackgroundColour(colors[1])
        self.victory.SetBorderColor(colors[0])
        self.victory.SetBarColor(colors[2])

        self.play_button = buttons.GenBitmapToggleButton(
            self, -1, self.all_graphics['button_play'],
            size=(34, 34), style = wx.BORDER_NONE)
        self.play_button.SetOwnBackgroundColour(colors[1])
        self.play_button.SetBitmapSelected(self.all_graphics['button_pause'])
        self.play_button.SetBackgroundColour(colors[1])
        self.play_button.Bind(wx.EVT_BUTTON, self.toggle_play)

        self.DoLayout()

    def DoLayout(self):
        main_sizer = wx.FlexGridSizer(1, 16)

        params = ['name', 'account', 'sectors']
        for param in params:
            main_sizer.Add(self.displayed['icon_' + param], 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)
            if not param == 'sectors':
                d = 100
            else:
                d = 330
            main_sizer.Add(self.displayed[param], 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, d)

        main_sizer.Add(self.victory, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        main_sizer.Add(self.play_button, 0, wx.ALIGN_CENTER_VERTICAL)

        self.SetSizer(main_sizer)

    def toggle_play(self, evt):
        status = self.play_button.GetValue()
        self.connection.Send({'action': 'run_ticks', 'status': status})

    def set_max(self, maximum):
        self.middle = int(maximum / 2)

    def update_status(self, status):

        for param, value in status.items():
            if param == 'diff':
                val = (self.middle + float(value)) / (2 * self.middle)
                val = int(round(float(self.middle + value)/(2 * self.middle)*100))
                self.victory.SetValue(val)
                self.victory.Refresh()
            elif param == 'sectors':
                self.displayed[param].SetLabel(', '.join(map(lambda x: str(x), value)))
            elif param == 'account':
                self.displayed[param].SetLabel(str(int(value)) + ' $')
            else:
                self.displayed[param].SetLabel(str(value))

        # self.Layout()

    def update_play(self, status):
        self.play_button.SetValue(status)


class BottomPanel(wx.Panel):

    def __init__(self, parent, all_graphics, connection):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, size=(1330, 370))
        self.all_graphics = all_graphics
        self.connection = connection
        self.game_obj = {}
        self.game_parameters = {}
        self.current_selection = []

        self.action_panel = ActionPanel(self, self.all_graphics)
        self.detail_panel = SelectionDetails(self, self.all_graphics)
        self.summary = Summary(self, self.all_graphics)

        self.DoLayout()

    def DoLayout(self):

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detail_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.top_sizer.AddSpacer(5)
        self.top_sizer.Add(self.action_panel, 0, wx.RIGHT, 60)
        self.top_sizer.Add(wx.StaticLine(self, size=(2, 50)))
        self.top_sizer.Add(self.summary, 0, wx.LEFT, 60)
        self.detail_panel_sizer.Add(self.detail_panel)

        self.main_sizer.Add(self.top_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 10)
        self.main_sizer.Add(wx.StaticLine(self, size=(1330, 2)))
        self.main_sizer.Add(self.detail_panel_sizer, 0, wx.EXPAND)

        self.SetSizer(self.main_sizer)

    def update_objects(self, game_obj):
        self.game_obj = game_obj

        # update the units if presented
        self.update_displayed()

        # Propagate to summary and actions
        self.summary.update_objects(self.game_obj)
        self.update_allowed_actions()

    def update_game_parameters(self, game_parameters):
        self.game_parameters = game_parameters

    def update_displayed(self):
        if isinstance(self.detail_panel, SelectionDetails):
            # Find all the delays
            updated = {}
            for o_id in self.current_selection:
                if o_id in self.game_obj['groups'].keys():
                    group = self.game_obj['groups'][o_id]
                    for u_id, unit in group['units'].items():
                        updated[(o_id, u_id)] = unit

                elif o_id in self.game_obj['buildings'].keys():
                    updated[o_id] = self.game_obj['buildings'][o_id]

                elif o_id in self.game_obj['transporter'].keys():
                    updated[o_id] = self.game_obj['transporter'][o_id]

            self.detail_panel.update_displayed(updated)

    def update_allowed_actions(self):
        sel = {'groups': [], 'transporter': [], 'buildings': []}

        # check delay of all units
        some_delayed = False
        some_not_delayed = False
        some_in_building = False
        some_not_in_building = False
        some_protected = False
        some_not_protected = False
        some_transported = False
        some_not_transported = False

        protect = False
        unprotect = False
        enter_building = False
        exit_building = False
        exit_transporter = False

        num_units = 0
        unit_types = []

        # Check which type it is for the details
        for new_id in self.current_selection:
            if new_id in self.game_obj['groups'].keys():
                sel['groups'].append(new_id)

                if self.game_obj['groups'][new_id]['transporter'] != -1 and exit_transporter == False:
                    some_transported = True
                    exit_transporter = True
                elif self.game_obj['groups'][new_id]['transporter'] == -1 and exit_transporter == True:
                    some_not_transported = True
                    exit_transporter = False

                for u_id, unit in self.game_obj['groups'][new_id]['units'].items():

                    num_units += 1
                    unit_types.append(unit['parameters']['unit_type'])

                    if unit['protected']:
                        if unit['delay'] == 0:
                            unprotect = True
                        some_protected = True
                    else:
                        if unit['delay'] == 0:
                            protect = True
                        some_not_protected = True

                    if unit['delay'] != 0:
                        some_delayed = True
                    else:
                        some_not_delayed = True

                    if unit['building'] != -1:
                        some_in_building = True
                        if unit['delay'] == 0:
                            exit_building = True
                    else:
                        some_not_in_building = True
                        if unit['delay'] == 0:
                            enter_building = True

            elif new_id in self.game_obj['transporter'].keys():
                num_units += 1
                sel['transporter'].append(new_id)

                if self.game_obj['transporter'][new_id]['delay'] != 0:
                    some_delayed = True
                else:
                    some_not_delayed = True

            elif new_id in self.game_obj['buildings'].keys():
                num_units += 1
                sel['buildings'].append(new_id)

                if self.game_obj['buildings'][new_id]['delay'] != 0:
                    some_delayed = True
                else:
                    some_not_delayed = True

        # Update the allowed actions
        allowed_actions = []

        # Rename if only one id is selected
        if len(sel['groups'] + sel['transporter'] + sel['buildings']) == 1:
            allowed_actions.append('rename')

        # Move is allowed if:
        # any groups, transporter and no buildings
        if (sel['groups'] or sel['transporter']) and not sel['buildings']:
            # if no delay, protected or in building
            if not some_protected and not some_delayed and not some_in_building:
                allowed_actions.append('move')

        # fight allowed if any not delayed
        if some_not_delayed:
            allowed_actions.append('fight')

        # move units between groups is allowed if only groups selected
        if sel['groups'] and not sel['transporter'] and not sel['buildings']:
            allowed_actions.append('move_units')

        # protect & unprotect
        if protect and not sel['buildings'] and not sel['transporter'] and not some_transported and not some_in_building:
            allowed_actions.append('protect')
        if unprotect and not sel['buildings'] and not sel['transporter']:
            allowed_actions.append('unprotect')

        # check if transporter can be loaded:
        if len(sel['transporter']) == 1 and len(sel['groups']) == 1 and not sel['buildings']:
            # only unique unit types
            unit_types = list(set(unit_types))

            if not some_protected and not some_delayed and not some_in_building and not exit_transporter:
                # check if transporter transports the right type
                # check if transporter has enough capacity
                trans = self.game_obj['transporter'][sel['transporter'][0]]
                cap = trans['parameters']['capacity']
                num_in = 0
                for g_id in trans['current']:
                    num_in += len(self.game_obj['groups'][g_id]['units'])

                if num_units - 1 <= cap - num_in:
                    if len(unit_types) == 1 and unit_types[0] == trans['parameters']['transports']:
                        allowed_actions.append('load_transporter')

        # check if unit can be unloaded from transporter
        if exit_transporter and not sel['transporter'] and not sel['buildings'] and not some_delayed:
            allowed_actions.append('unload_group')

        if exit_building and len(sel['groups']) == 1 and not sel['transporter'] and not sel['buildings']:
            allowed_actions.append('exit_building')

        if enter_building and sel['groups'] and not sel['transporter'] and len(sel['buildings']) == 1 and not some_transported and some_not_protected:
            allowed_actions.append('enter_building')

        self.action_panel.update_allowed_actions(allowed_actions)

    def update_selection(self, selected_ids):
        self.current_selection = selected_ids

        sel = {'groups': [], 'transporter': [], 'buildings': []}

        # Check which type it is for the details
        for new_id in self.current_selection:
            if new_id in self.game_obj['groups'].keys():
                sel['groups'].append(new_id)
            elif new_id in self.game_obj['transporter'].keys():
                sel['transporter'].append(new_id)
            elif new_id in self.game_obj['buildings'].keys():
                sel['buildings'].append(new_id)

        # clear sizer and destroy previous panel
        self.detail_panel_sizer.Clear(True)
        # if self.detail_panel:
        #    self.detail_panel.Destroy()

        # Shop
        if len(sel['buildings']) == 1 and not sel['groups'] and not sel['transporter']:
            b_id = sel['buildings'][0]
            build = self.game_obj['buildings'][b_id]

            self.detail_panel = Shop(self, self.all_graphics,
                                     self.connection, self.game_parameters, build, b_id)
            self.detail_panel_sizer.Add(self.detail_panel, 0, wx.EXPAND)

        # elif len(sel['transporter']) == 1 and not sel['groups'] and not sel['buildings']:
        #    trans = self.game_obj['transporter'][sel['transporter'][0]]
        #    self.detail_panel = False

        # general details (unit list)
        elif sel['groups'] or sel['buildings'] or sel['transporter']:
            selection = {'groups': {}, 'transporter': {}, 'buildings': {}}
            for g_id in sel['groups']:
                selection['groups'][g_id] = self.game_obj['groups'][g_id]
            for b_id in sel['buildings']:
                selection['buildings'][b_id] = self.game_obj['buildings'][b_id]
            for b_id in sel['transporter']:
                selection['transporter'][
                    b_id] = self.game_obj['transporter'][b_id]

            self.detail_panel = SelectionDetails(
                self, self.all_graphics, selection)
            self.detail_panel_sizer.Add(self.detail_panel, 0, wx.EXPAND)

        else:
            self.detail_panel = False

        self.detail_panel_sizer.Layout()

        # update summary and actions
        self.summary.update_selection(selected_ids)
        self.update_allowed_actions()


class Summary(wx.Panel):

    def __init__(self, parent, all_graphics):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.all_graphics = all_graphics
        self.SetBackgroundColour(colors[1])
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.SetMinSize((600, 50))
        self.game_obj = {}
        self.selected_ids = []

        # Order fields in sizers
        self.vert_sizers = {}
        self.hor_sizers = {}

        def create_hor_sizer(el1, el2, spacer=15):
            hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
            hor_sizer.Add(el1)
            hor_sizer.AddSpacer(spacer)
            hor_sizer.Add(el2)
            return hor_sizer

        # Create Fields for text
        self.text_fields = {}
        self.images = {}

        field_names = ['name', 'num_units', 'life', 'attack',
                       'shield', 'delay', 'walk_dist', 'shoot_dist',
                       'delay_walk', 'delay_shoot', 'sectors']

        image_names = [
            'unknown_icon', 'icon_group', 'icon_life', 'icon_average_attack',
            'icon_shield', 'icon_delay', 'icon_walk_dist', 'icon_shoot_dist',
            'icon_delay_walk', 'icon_delay_shoot', 'icon_sector']

        new_vert_sizer = True
        cur_sizer = -1

        for i in range(len(field_names)):
            name = field_names[i]
            image = image_names[i]
            self.text_fields[name] = wx.StaticText(self, -1, '    ')
            self.text_fields[name].SetFont(fonts['parameter'])

            if name != 'name':
                spacer = 15
                self.images[i] = wx.StaticBitmap(self, -1, all_graphics[image])
            else:
                spacer = 0
                self.images[i] = wx.BoxSizer(wx.HORIZONTAL)

            spacer_vert = 0
            if new_vert_sizer:
                spacer_vert = 10
                cur_sizer += 1
                if cur_sizer != 0:
                    self.main_sizer.Add(self.vert_sizers[cur_sizer - 1])
                    self.main_sizer.AddSpacer(50)
                self.vert_sizers[cur_sizer] = wx.BoxSizer(wx.VERTICAL)

            hor_sizer = create_hor_sizer(
                self.images[i], self.text_fields[name], spacer)
            self.vert_sizers[cur_sizer].Add(hor_sizer, 0, wx.BOTTOM, spacer_vert)

            new_vert_sizer = not new_vert_sizer

        self.main_sizer.Add(self.vert_sizers[cur_sizer])
        self.main_sizer.AddSpacer(25)

        # Display Peak meter with 6 bands and only one led per band
        # self.shoot_dist = PM.PeakMeterCtrl(self, -1, style=wx.NO_BORDER, agwStyle=PM.PM_VERTICAL)
        # self.shoot_dist.SetMeterBands(5, 1)
        # self.shoot_dist.SetBackgroundColour('#60CC69')
        # self.shoot_dist.SetBandsColour('#FFFFFF', '#FFFFFF', '#FFFFFF')
        # Generate fake data for peaks
        # self.shoot_dist.SetData([100, 90,60,30,0], 0, 5)
        # self.peak_sizer = wx.BoxSizer(wx.VERTICAL)
        # self.peak_sizer.SetDimension(1,1,50,50)
        # self.peak_sizer.Add(self.shoot_dist)
        # self.main_sizer.Add(self.peak_sizer)
        self.SetSizer(self.main_sizer)
        self.Layout()

    def update_objects(self, game_obj):
        self.game_obj = game_obj

        # delete ids which are not alive anymore
        all_keys = self.game_obj['groups'].keys() + self.game_obj[
            'transporter'].keys()
        all_keys += self.game_obj['buildings'].keys()
        for ind in self.selected_ids:
            if ind not in all_keys:
                self.selected_ids.remove(ind)

        self.update_selection(self.selected_ids)

    def update_selection(self, selected_ids):
        self.selected_ids = selected_ids

        par = {
            'name': '', 'num_units': 0, 'life': 0, 'max_life': 0, 'attack': 0, 'shield': 0,
            'max_delay': 0, 'min_delay': 1000, 'min_walk_dist': 1000, 'max_walk_dist': 0,
            'min_delay_shoot': 1000, 'max_delay_shoot': 0,
            'min_delay_walk': 1000, 'max_delay_walk': 0,
            'min_shoot_dist': 1000, 'max_shoot_dist': 0, 'sectors': []
        }

        all_obj = []

        some_no_walk_dist = False
        some_walk_dist = False

        for ind in selected_ids:
            sector = False
            if ind in self.game_obj['groups'].keys():
                sector = self.game_obj['groups'][ind]['sector']
                for unit in self.game_obj['groups'][ind]['units'].values():
                    if unit['protected'] or unit['building'] != -1 or unit['delay'] != 0:
                        some_no_walk_dist = True
                    else:
                        some_walk_dist = True

                    all_obj.append(unit)

            elif ind in self.game_obj['transporter'].keys():
                sector = self.game_obj['transporter'][ind]['sector']
                if self.game_obj['transporter'][ind]['delay'] != 0:
                    some_no_walk_dist = True
                else:
                    some_walk_dist = True

                all_obj.append(self.game_obj['transporter'][ind])

            elif ind in self.game_obj['buildings'].keys():
                some_no_walk_dist = True
                sector = self.game_obj['buildings'][ind]['sector']
                all_obj.append(self.game_obj['buildings'][ind])

            if sector:
                if sector not in par['sectors']:
                    par['sectors'].append(sector)

        for obj in all_obj:
            obj_par = obj['parameters']

            par['life'] += obj_par['life']
            par['max_life'] += obj_par['max_life']
            par['attack'] += float(
                obj_par['attack_min'] + obj_par['attack_max']) / 2
            par['shield'] += obj_par['shield']

            try:
                wd = obj_par['walk_dist']
                dw = obj_par['delay_walk']

                if wd < par['min_walk_dist']:
                    par['min_walk_dist'] = wd

                if wd > par['max_walk_dist']:
                    par['max_walk_dist'] = wd

                if dw < par['min_delay_walk']:
                    par['min_delay_walk'] = dw

                if dw > par['max_delay_walk']:
                    par['max_delay_walk'] = dw

            except KeyError:
                pass

            if obj_par['shoot_dist'] < par['min_shoot_dist']:
                par['min_shoot_dist'] = obj_par['shoot_dist']

            if obj_par['shoot_dist'] > par['max_shoot_dist']:
                par['max_shoot_dist'] = obj_par['shoot_dist']

            if obj_par['delay_shoot'] < par['min_delay_shoot']:
                par['min_delay_shoot'] = obj_par['delay_shoot']

            if obj_par['delay_shoot'] > par['max_delay_shoot']:
                par['max_delay_shoot'] = obj_par['delay_shoot']

            if obj['delay'] > par['max_delay']:
                par['max_delay'] = obj['delay']

            if obj['delay'] < par['min_delay']:
                par['min_delay'] = obj['delay']

        par['num_units'] = len(all_obj)
        if par['num_units'] > 1:
            par['name'] = 'Multiple'
        elif par['num_units'] == 1:
            par['name'] = obj_par['name']
        else:
            par['name'] = 'No Selection'

        # set all the parameters
        # Simple parameters
        for p in ['name', 'attack', 'shield', 'num_units', 'sectors']:
            if p == 'name':
                te = str(par[p])
            elif p == 'sectors':
                te = ', '.join(map(lambda x: str(x), par[p]))
            else:
                te = str(int(par[p]))

            self.text_fields[p].SetLabel(te)

        if some_no_walk_dist:
            par['min_walk_dist'] = 0

        # ranges
        def set_range(parameter, min_val, max_val):
            if min_val != 1000:
                if min_val != max_val:
                    text = '{0}-{1}'.format(int(min_val), int(max_val))
                else:
                    text = str(max_val)
            else:
                text = '0'
            self.text_fields[parameter].SetLabel(text)

        if some_walk_dist:
            set_range('walk_dist', par['min_walk_dist'], par['max_walk_dist'])
        else:
            self.text_fields['walk_dist'].SetLabel('0')

        set_range('life', par['life'], par['max_life'])
        set_range('shoot_dist', par['min_shoot_dist'], par['max_shoot_dist'])
        set_range('delay_walk', par['min_delay_walk'], par['max_delay_walk'])
        set_range(
            'delay_shoot', par['min_delay_shoot'], par['max_delay_shoot'])
        set_range('delay', par['min_delay'], par['max_delay'])


class MoveUnits(wx.Dialog):

    def __init__(self, parent, selected_groups, all_graphics, connection):
        wx.Dialog.__init__(self, parent,
                           title='Move Units between Groups', size=(800, 600))
        self.all_graphics = all_graphics
        self.connection = connection
        self.selected_groups = selected_groups

        self.top_level_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled_panel = scrolled.ScrolledPanel(
            self, -1, size=(790, 500))

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.displayed = {}
        self.sizers = {}
        self.choices = {}

        self.group_choices = [str(k) for k in selected_groups.keys()]
        self.group_choices.append('New Group')

        for g_id, group in selected_groups.items():
            disp = str(g_id) + ': ' + group['name']
            self.main_sizer.Add(
                wx.StaticText(self.scrolled_panel, label=disp))
            self.sizers[g_id] = wx.BoxSizer(wx.HORIZONTAL)
            for u_id, unit in group['units'].items():
                u_sizer = wx.BoxSizer(wx.VERTICAL)
                self.displayed[(g_id, u_id)] = Unit(
                    self.scrolled_panel, g_id, u_id, unit, self.all_graphics)

                self.choices[(g_id, u_id)] = wx.Choice(self.scrolled_panel,
                                                       -1, size=(100, 50), choices = self.group_choices)

                self.choices[(g_id, u_id)].SetSelection(
                    self.group_choices.index(str(g_id)))

                u_sizer.Add(self.displayed[(g_id, u_id)])
                u_sizer.Add(self.choices[(g_id, u_id)])

                self.sizers[g_id].Add(u_sizer)

            self.main_sizer.Add(self.sizers[g_id])
            self.main_sizer.AddSpacer(5)

        self.scrolled_panel.SetSizer(self.main_sizer)

        self.scrolled_panel.SetupScrolling(True, True)

        self.submit_button = wx.BitmapButton(
            self, -1, bitmap=self.all_graphics['button_ok'])
        self.submit_button.Bind(wx.EVT_BUTTON, self.on_submit)

        self.cancel_button = wx.BitmapButton(
            self, -1, bitmap=self.all_graphics['button_back'])
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        self.new_name = wx.TextCtrl(self, -1, '')

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.Add(wx.StaticText(self, -1, 'Name of new group:'))
        bottom_sizer.AddSpacer(5)
        bottom_sizer.Add(self.new_name)
        bottom_sizer.AddSpacer(10)
        bottom_sizer.Add(self.submit_button)
        bottom_sizer.AddSpacer(10)
        bottom_sizer.Add(self.cancel_button)

        self.top_level_sizer.Add(self.scrolled_panel)
        self.top_level_sizer.AddSpacer(10)
        self.top_level_sizer.Add(bottom_sizer)

        self.SetSizer(self.top_level_sizer)

        self.Layout()

    def on_cancel(self, evt):
        self.EndModal(True)

    def on_submit(self, evt):
        changes = {}
        for group, choice in self.choices.items():
            sel = choice.GetStringSelection()
            if sel != 'New Group':
                changes[group] = int(sel)
            else:
                changes[group] = -1

        name = self.new_name.GetValue()
        self.connection.Send(
            {'action': 'move_units', 'changes': changes, 'new_name': name})
        self.EndModal(True)


class ActionCategory(wx.Dialog):

    def __init__(self, parent, title, actions, all_graphics):
        wx.Dialog.__init__(self, parent, title=title, size=(200, 250))
        self.all_graphics = all_graphics
        self.selected_action = False

        self.SetBackgroundColour(colors[1])

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        # Make e list of all actions (scrolled): the action_panel
        self.action_panel = scrolled.ScrolledPanel(self, -1, size=(170, 160))

        self.action_sizer = wx.BoxSizer(wx.VERTICAL)
        self.all_actions = {}

        # Create each action (a button and a description)
        for name, action in actions.items():
            hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.all_actions[name] = wx.BitmapButton(
                self.action_panel, -1, self.all_graphics['button_action'],
                name=name, size=(20, 20), style = wx.BORDER_NONE)
            self.all_actions[name].Bind(wx.EVT_BUTTON, self.on_click)

            label = name + ' '
            if action['price'] > 0:
                label += ', ' + str(int(action['price'])) + '$'

            if action['delay'] > 0:
                label += ', wait ' + str(int(action['delay']))

            if action['num_uses'] != -1:
                label += ', ' + str(action['num_uses']) + 'x'

            hor_sizer.Add(self.all_actions[name])
            hor_sizer.AddSpacer(10)
            hor_sizer.Add(wx.StaticText(self.action_panel, -1, label))
            self.action_sizer.Add(hor_sizer)
            self.action_sizer.AddSpacer(10)

        self.action_panel.SetSizer(self.action_sizer)

        self.action_panel.SetupScrolling(False, True)

        self.quit_btn = wx.BitmapButton(
            self, -1, self.all_graphics['button_back'], style=wx.BORDER_NONE)
        self.quit_btn.SetBackgroundColour(colors[1])
        self.quit_btn.Bind(wx.EVT_BUTTON, self.on_quit)

        self.main_sizer.Add(self.action_panel)
        self.main_sizer.AddSpacer(15)
        self.main_sizer.Add(self.quit_btn)

        self.SetSizer(self.main_sizer)

    def on_click(self, evt):
        name = evt.GetEventObject().GetName()
        self.selected_action = name
        self.EndModal(True)

    def on_quit(self, evt):
        self.EndModal(False)


class Shop(wx.Panel):

    def __init__(self, parent, all_graphics, connection, game_parameters, building, b_id):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.game_parameters = game_parameters
        self.all_graphics = all_graphics
        self.connection = connection
        self.building = building

        self.units = {}
        self.current_group = []

        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        def add_line():
            line = wx.StaticLine(self, size=(2, 310))
            self.main_sizer.AddSpacer(5)
            self.main_sizer.Add(line)
            self.main_sizer.AddSpacer(5)

        add_line()

        self.build_displayed = ObjSummary(
            self, b_id, building, all_graphics, True)
        self.main_sizer.Add(self.build_displayed)
        add_line()

        if len(building['parameters']['shop_units']) + len(building['parameters']['shop_transporter']) > 0:
            self.main_sizer.AddSpacer(30)

            # get all possible units
            def create_unit(ind, basic_params):
                '''returns a sizer'''
                u = {}
                u['main_sizer'] = wx.BoxSizer(wx.VERTICAL)
                u['top_sizer'] = wx.BoxSizer(wx.HORIZONTAL)
                u['middle_sizer'] = wx.BoxSizer(wx.HORIZONTAL)
                u['icon_grid'] = wx.GridSizer(3, 5)

                u['top_right_sizer'] = wx.BoxSizer(wx.VERTICAL)
                u['button_sizer'] = wx.BoxSizer(wx.VERTICAL)
                u['top_button_sizer'] = wx.BoxSizer(wx.HORIZONTAL)
                u['bottom_button_sizer'] = wx.BoxSizer(wx.HORIZONTAL)

                try:
                    image = self.all_graphics['unit_' + str(ind)]
                except KeyError:
                    image = self.all_graphics['unknown']

                u['image'] = wx.BitmapButton(self, bitmap=image, name=str(
                    ind) + ',image', style=wx.BORDER_NONE)
                u['image'].Bind(wx.EVT_BUTTON, self.on_button)
                u['image'].SetBackgroundColour(colors[1])

                u['name'] = wx.StaticText(self, -1, basic_params['name'])
                u['price'] = wx.StaticText(
                    self, -1, str(basic_params['price']) + '$')
                u['num_selected'] = wx.StaticText(self, -1, '0')

                for but in ['button_plus', 'button_minus', 'button_5', 'button_10']:
                    u[but] = wx.BitmapButton(
                        self, bitmap=self.all_graphics[but],
                        name=str(ind) + ',' + but, style=wx.BORDER_NONE)
                    u[but].Bind(wx.EVT_BUTTON, self.on_button)
                    u[but].SetBackgroundColour(colors[1])

                # Buttons
                u['top_button_sizer'].Add(u['button_plus'])
                u['top_button_sizer'].AddSpacer(5)
                u['top_button_sizer'].Add(u['button_minus'])

                u['bottom_button_sizer'].Add(u['button_5'])
                u['bottom_button_sizer'].AddSpacer(5)
                u['bottom_button_sizer'].Add(u['button_10'])

                u['button_sizer'].Add(u['top_button_sizer'])
                u['button_sizer'].AddSpacer(5)
                u['button_sizer'].Add(u['bottom_button_sizer'])

                # Top part
                u['top_right_sizer'].Add(u['name'])
                u['top_right_sizer'].AddSpacer(5)
                u['top_right_sizer'].Add(u['price'])

                u['top_sizer'].Add(u['image'])
                u['top_sizer'].AddSpacer(5)
                u['top_sizer'].Add(u['top_right_sizer'])

                # Middle Part
                u['middle_sizer'].Add(u['num_selected'])
                u['middle_sizer'].AddSpacer(5)
                u['middle_sizer'].Add(u['button_sizer'])

                # Parameter part
                u_p = basic_params
                params = [('life', str(int(u_p['life']))),
                          ('shield', str(int(u_p['shield']))),
                          ('shoot_dist', str(int(u_p['shoot_dist']))),
                          ('walk_dist', str(int(u_p['walk_dist']))),
                          ('delay_shoot', str(int(u_p['delay_shoot']))),
                          ('delay_walk', str(int(u_p['delay_walk']))),
                          ('attack', '{0}-{1}'.format(int(u_p['attack_min']), int(u_p['attack_max'])))
                          ]

                u['parameter_sizer'] = wx.FlexGridSizer(3, 5)

                spacer = True

                for param, value in params:
                    image = 'icon_' + param
                    params_image = wx.StaticBitmap(self, wx.ID_ANY, all_graphics[image])
                    params_value = wx.StaticText(self, -1, value)
                    params_value.SetFont(fonts['parameter'])

                    u['parameter_sizer'].Add(params_image, 0, wx.ALL, 5)
                    u['parameter_sizer'].Add(params_value, 0, wx.ALIGN_CENTER_VERTICAL)

                    if spacer:
                        u['parameter_sizer'].AddSpacer(20)

                    spacer = not spacer

                # General Layout

                u['main_sizer'].Add(u['top_sizer'])
                u['main_sizer'].AddSpacer(10)
                u['main_sizer'].Add(u['middle_sizer'])
                u['main_sizer'].AddSpacer(10)
                u['main_sizer'].Add(u['icon_grid'])
                u['main_sizer'].AddSpacer(10)
                u['main_sizer'].Add(u['parameter_sizer'])

                return u

            def create_transporter(ind, basic_params):
                u = {}
                u['main_sizer'] = wx.BoxSizer(wx.VERTICAL)
                u['top_sizer'] = wx.BoxSizer(wx.HORIZONTAL)
                u['top_left_sizer'] = wx.BoxSizer(wx.VERTICAL)
                u['top_right_sizer'] = wx.BoxSizer(wx.VERTICAL)

                u['name'] = wx.StaticText(self, -1, basic_params['name'])
                u['price'] = wx.StaticText(
                    self, -1, str(basic_params['price']) + '$')

                try:
                    image = self.all_graphics['transporter_' + str(ind)]
                except KeyError:
                    image = self.all_graphics['unknown']

                u['image'] = wx.StaticBitmap(
                    self, bitmap=image, style=wx.BORDER_NONE)
                u['image'].SetBackgroundColour(colors[1])

                u['buy'] = wx.BitmapButton(self, bitmap=self.all_graphics['button_cash'],
                                           name=str(ind), style=wx.BORDER_NONE)
                u['buy'].Bind(wx.EVT_BUTTON, self.buy_transporter)
                u['buy'].SetBackgroundColour(colors[1])

                u['top_left_sizer'].Add(u['name'])
                u['top_left_sizer'].AddSpacer(5)
                u['top_left_sizer'].Add(u['image'])

                u['top_right_sizer'].Add(u['price'])
                u['top_right_sizer'].AddSpacer(5)
                u['top_right_sizer'].Add(u['buy'])

                u['top_sizer'].Add(u['top_left_sizer'])
                u['top_sizer'].AddSpacer(5)
                u['top_sizer'].Add(u['top_right_sizer'])

                # Parameter part
                u_p = basic_params
                params = [('life', str(int(u_p['life']))),
                          ('shield', str(int(u_p['shield']))),
                          ('shoot_dist', str(int(u_p['shoot_dist']))),
                          ('walk_dist', str(int(u_p['walk_dist']))),
                          ('delay_shoot', str(int(u_p['delay_shoot']))),
                          ('delay_walk', str(int(u_p['delay_walk']))),
                          ('attack', '{0}-{1}'.format(int(u_p['attack_min']), int(u_p['attack_max'])))
                          ]

                u['parameter_sizer'] = wx.FlexGridSizer(3, 5)

                spacer = True

                for param, value in params:
                    image = 'icon_' + param
                    params_image = wx.StaticBitmap(self, wx.ID_ANY, all_graphics[image])
                    params_value = wx.StaticText(self, -1, value)
                    params_value.SetFont(fonts['parameter'])

                    u['parameter_sizer'].Add(params_image, 0, wx.ALL, 5)
                    u['parameter_sizer'].Add(params_value, 0, wx.ALIGN_CENTER_VERTICAL)

                    if spacer:
                        u['parameter_sizer'].AddSpacer(20)

                    spacer = not spacer

                # General Layout

                u['main_sizer'].Add(u['top_sizer'])
                u['main_sizer'].AddSpacer(10)
                u['main_sizer'].Add(u['parameter_sizer'])

                return u

            self.summary_sizer = wx.BoxSizer(wx.VERTICAL)
            self.tot_price = wx.StaticText(self, -1, '0$                  ')
            self.name = wx.TextCtrl(self, -1, '')

            self.buy_button = wx.BitmapButton(
                self, bitmap=self.all_graphics['action_buy'],
                size=(45, 45), style = wx.BORDER_NONE)
            self.buy_button.Bind(wx.EVT_BUTTON, self.buy_group)
            self.buy_button.SetBackgroundColour(colors[1])

            self.summary_sizer.Add(self.tot_price)
            self.summary_sizer.AddSpacer(15)
            self.summary_sizer.Add(self.name)
            self.summary_sizer.AddSpacer(15)
            self.summary_sizer.Add(self.buy_button)

            self.main_sizer.Add(self.summary_sizer)
            add_line()

            self.all_units = {}
            self.all_transporters = {}
            for ind in building['parameters']['shop_units']:
                unit = game_parameters['unit_parameters'][ind]
                self.all_units[ind] = create_unit(ind,
                                                  unit['basic_parameters'])
                self.main_sizer.Add(self.all_units[ind]['main_sizer'])
                add_line()

            for ind in building['parameters']['shop_transporter']:
                trans = game_parameters['transport_parameters'][ind]
                self.all_transporters[
                    ind] = create_transporter(ind, trans['basic_parameters'])
                self.main_sizer.Add(self.all_transporters[ind]['main_sizer'])
                add_line()

        self.SetSizer(self.main_sizer)

    def on_button(self, evt):
        name = evt.GetEventObject().GetName()
        res = name.split(',')
        unit_id = int(res[0])
        button = res[1]

        if button in ('button_plus', 'image'):
            self.current_group.append(unit_id)
        elif button == 'button_5':
            for i in range(5):
                self.current_group.append(unit_id)
        elif button == 'button_10':
            for i in range(10):
                self.current_group.append(unit_id)
        elif button == 'button_minus':
            try:
                self.current_group.remove(unit_id)
            except:
                pass

        self.update_summary()

    def update_summary(self):
        tot_price = 0
        for unit in self.current_group:
            tot_price += self.game_parameters[
                'unit_parameters'][unit]['basic_parameters']['price']

        self.tot_price.SetLabel(str(tot_price) + '$')

        co = Counter(self.current_group)

        for unit in self.all_units.keys():
            if unit in co.keys():
                occ = co[unit]
            else:
                occ = 0
            self.all_units[unit]['num_selected'].SetLabel(str(occ))

    def buy_group(self, evt):
        if len(self.current_group) > 0:
            name = self.name.GetValue()
            self.connection.Send(
                {"action": "buy_group", "units": self.current_group,
                 "name": name, 'sector': self.building['sector']})

    def buy_transporter(self, evt):
        t_id = int(evt.GetEventObject().GetName())
        name = self.name.GetValue()
        self.connection.Send({"action": "buy_transporter", "transporter": t_id,
                             'name': name, 'sector': self.building['sector']})


class SelectionDetails(wx.Panel):

    '''Displayed overall details:
    Attack (per distance), Life, walk distance, some units in building,
    some units protected, group transported, number of units,
    average age of units, average elite of units, delay until next unit is free'''
    def __init__(self, parent, all_graphics, selection={}):
        wx.Panel.__init__(
            self, parent=parent, id=wx.ID_ANY, size=(1330, 310))
        self.all_graphics = all_graphics
        self.SetBackgroundColour(colors[1])
        self.selection = selection

        self.units = {}

        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # all units
        self.unit_panel = scrolled.ScrolledPanel(self, -1, size=(1330, 310))
        self.detail_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.displayed_objects = {}

        def add_line():
            line = wx.StaticLine(self.unit_panel, size=(2, 310))
            self.detail_sizer.AddSpacer(5)
            self.detail_sizer.Add(line, 0, wx.EXPAND)
            self.detail_sizer.AddSpacer(5)

        if selection:
            add_line()
            for b_id, building in selection['buildings'].items():
                self.displayed_objects[b_id] = ObjSummary(
                    self.unit_panel, b_id, building, self.all_graphics, is_building=True)
                self.detail_sizer.Add(self.displayed_objects[b_id])
                add_line()

            for t_id, trans in selection['transporter'].items():
                self.displayed_objects[t_id] = ObjSummary(
                    self.unit_panel, t_id, trans, self.all_graphics, is_building=False)
                self.detail_sizer.Add(self.displayed_objects[t_id])
                add_line()

            for g_id, group in selection['groups'].items():
                for u_id, unit in group['units'].items():
                    self.displayed_objects[(g_id, u_id)] = Unit(
                        self.unit_panel, g_id, u_id, unit, self.all_graphics)
                    self.detail_sizer.Add(self.displayed_objects[(g_id, u_id)])
                    add_line()

        self.unit_panel.SetSizer(self.detail_sizer)

        self.main_sizer.Add(self.unit_panel)

        self.unit_panel.SetupScrolling(True, False)

        self.SetSizer(self.main_sizer)

    def update_displayed(self, updated_objects):

        for coord, obj in updated_objects.items():
            try:
                self.displayed_objects[coord].update_parameters(obj)
            except KeyError:
                pass


class Unit_IGNORE(wx.Panel):

    '''Displayed as image: unit, elite, building, protected,

    as text: delay left, life, attack, dist shoot, dist walk, age, total_damage
    actions as buttons in separate scrolled panel'''

    def __init__(self, parent, g_id, u_id, unit, all_graphics):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, size=(150, 310))
        # self.SetMinSize((150, 300))
        self.all_graphics = all_graphics
        self.unit = unit
        self.u_id = u_id
        self.g_id = g_id

        try:
            unit_bmp = all_graphics['unit_' + str(unit['parameters']['id'])]
        except KeyError:
            unit_bmp = all_graphics['unknown']

        try:
            elite = 'rank_' + str(int(unit['parameters']['elite']))
            elite_bmp = all_graphics[elite]
        except KeyError:
            elite_bmp = all_graphics['rank_8']

        if unit['building'] == -1:
            b_bmp = 'icon_not_in_building'
        else:
            b_bmp = 'icon_in_building'

        try:
            building_bmp = all_graphics[b_bmp]
        except KeyError:
            building_bmp = all_graphics['unknown']

        if unit['protected']:
            p_bmp = 'icon_protected'
        else:
            p_bmp = 'icon_not_protected'

        protection_bmp = all_graphics[p_bmp]

        name = unit['parameters']['name'] + ' ' + unit['name']

        # display all parameters

        self.params = ['life', 'shield', 'shoot_dist', 'walk_dist', 'attack', 'delay']

        self.params_images = {}
        self.params_value = {}

        spacer = True

        for param in self.params:
            image = 'icon_' + param
            self.params_images[image] = wx.StaticBitmap(
                self, wx.ID_ANY, all_graphics[image])
            self.params_value[param] = wx.StaticText(self, -1, '')

        # Make e list of all actions (scrolled): the action_panel
        self.action_panel = scrolled.ScrolledPanel(self, -1, size=(145, 50))

        self.all_actions = {}

        self.action_sizer = wx.BoxSizer(wx.VERTICAL)

        self.collected_actions = {'upgrade': {}, 'shop': {}, 'equipment': {}}
        # Create each action (a button and a description)
        for name, action in self.unit['parameters']['actions'].items():
            if action['category'] != 'standard':
                self.collected_actions[action['category']][name] = action

            else:
                hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
                self.all_actions[name] = wx.BitmapButton(
                    self.action_panel, -1, self.all_graphics['button_action'],
                    name=name, size=(20, 20), style = wx.BORDER_NONE)
                self.all_actions[name].Bind(wx.EVT_BUTTON, self.on_unit_action)

                label = name + ' '
                if action['price'] > 0:
                    label += ', ' + str(int(action['price'])) + '$'

                if action['delay'] > 0:
                    label += ', wait ' + str(int(action['delay']))

                if action['num_uses'] != -1:
                    label += ', ' + str(action['num_uses']) + 'x'

                hor_sizer.Add(self.all_actions[name])
                hor_sizer.AddSpacer(10)
                hor_sizer.Add(wx.StaticText(self.action_panel, -1, label))
                self.action_sizer.Add(hor_sizer)

        # shortcuts (action categories)
        self.shortcuts = {}
        self.shortcut_sizer = wx.BoxSizer(wx.HORIZONTAL)

        for sh in ['upgrade', 'shop', 'equipment']:
            if len(self.collected_actions[sh]) > 0:
                img = 'button_' + sh
                self.shortcuts[sh] = wx.BitmapButton(
                    self.action_panel, -1, self.all_graphics[img],
                    style=wx.BORDER_NONE, name=sh)
                self.shortcuts[sh].Bind(wx.EVT_BUTTON, self.on_action_category)

                self.shortcut_sizer.Add(self.shortcuts[sh])
                if sh != 'equipment':
                    self.shortcut_sizer.AddSpacer(10)

        self.DoLayout()
        self.update_parameters(unit)

    def DoLayout(self):
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_left_bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_left_sizer.Add(wx.StaticText(self, -1, ''))
        self.top_left_sizer.AddSpacer(10)

        bmp = self.all_graphics['unknown']
        icon = self.all_graphics['unknown_icon']
        self.top_left_bottom_sizer.Add(wx.StaticBitmap(self, -1, bmp))
        self.top_left_bottom_sizer.AddSpacer(10)
        self.top_left_bottom_sizer.Add(wx.StaticBitmap(self, -1, icon))

        self.top_right_sizer.Add(wx.StaticBitmap(self, -1, icon))
        self.top_right_sizer.AddSpacer(5)
        self.top_right_sizer.Add(wx.StaticBitmap(self, -1, icon))

        self.top_left_sizer.Add(self.top_left_bottom_sizer)
        self.top_sizer.Add(self.top_left_sizer)
        self.top_sizer.AddSpacer(10)
        self.top_sizer.Add(self.top_right_sizer)

        self.params_sizer = wx.GridSizer(3, 5)

        spacer = True
        for param in self.params:
            image = 'icon_' + param
            self.params_sizer.Add(self.params_images[image])
            self.params_sizer.Add(self.params_value[param])

            if spacer:
                self.params_sizer.AddSpacer(10)

            spacer = not spacer

        self.action_sizer.AddSpacer(5)
        self.action_sizer.Add(self.shortcut_sizer)

        self.action_panel.SetSizer(self.action_sizer)

        self.action_panel.SetupScrolling(False, True)

        self.main_sizer.Add(self.top_sizer)
        self.main_sizer.AddSpacer(15)
        self.main_sizer.Add(self.params_sizer)
        self.main_sizer.AddSpacer(15)
        self.main_sizer.Add(self.action_panel)

        self.SetSizer(self.main_sizer)

    def on_action_category(self, evt):
        category = evt.GetEventObject().GetName()
        actions = self.collected_actions[category]
        dlg = ActionCategory(self, category, actions, self.all_graphics)
        success = dlg.ShowModal()
        if success:
            action = dlg.selected_action
            new_event = ActionEvent(
                INITIATE_ACTION, self.GetId(), action_type='unit_action',
                o_id=self.g_id, u_id=self.u_id, action_name=action)
            dlg.Destroy()
            self.GetEventHandler().ProcessEvent(new_event)

    def update_parameters(self, new_obj):
        params = [(
            'life', '{0}/{1}'.format(int(new_obj['parameters']['life']), int(new_obj['parameters']['max_life']))),
            ('shield', str(int(new_obj['parameters']['shield']))),
            ('shoot_dist', str(int(new_obj[
                                   'parameters']['shoot_dist']))),
            ('walk_dist', str(int(new_obj['parameters']['walk_dist']))),
            ('attack', '{0}-{1}'.format(int(new_obj['parameters'][
                                            'attack_min']), int(new_obj['parameters']['attack_max']))),
            ('delay', str(int(new_obj['delay'])))
        ]

        for param, value in params:
            self.params_value[param].SetLabel(value)

    def on_unit_action(self, evt):
        action_name = evt.GetEventObject().GetName()
        # Create an Action Event with all the necessary parameters
        new_event = ActionEvent(
            INITIATE_ACTION, self.GetId(), action_type='unit_action',
            o_id=self.g_id, u_id=self.u_id, action_name=action_name)

        # Process Event (handled in Main Frame)
        self.GetEventHandler().ProcessEvent(new_event)


class Unit(wx.Panel):

    '''Displayed as image: unit, elite, building, protected,

    as text: delay left, life, attack, dist shoot, dist walk, age, total_damage
    actions as buttons in separate scrolled panel'''

    def __init__(self, parent, g_id, u_id, unit, all_graphics):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, size=(150, 310))
        # self.SetMinSize((150, 300))
        self.all_graphics = all_graphics
        self.unit = unit
        self.u_id = u_id
        self.g_id = g_id

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        try:
            unit_bmp = all_graphics['unit_' + str(unit['parameters']['id'])]
        except KeyError:
            unit_bmp = all_graphics['unknown']

        try:
            elite = 'rank_' + str(int(unit['parameters']['elite']))
            elite_bmp = all_graphics[elite]
        except KeyError:
            elite_bmp = all_graphics['rank_8']

        if unit['building'] == -1:
            b_bmp = 'icon_not_in_building'
        else:
            b_bmp = 'icon_in_building'

        try:
            building_bmp = all_graphics[b_bmp]
        except KeyError:
            building_bmp = all_graphics['unknown']

        if unit['protected']:
            p_bmp = 'icon_protected'
        else:
            p_bmp = 'icon_not_protected'

        protection_bmp = all_graphics[p_bmp]

        # Sizers
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_left_bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)

        name = unit['parameters']['name'] + ' ' + unit['name']
        self.top_left_sizer.Add(wx.StaticText(self, -1, name))
        self.top_left_sizer.AddSpacer(10)

        self.top_left_bottom_sizer.Add(wx.StaticBitmap(self, -1, unit_bmp))
        self.top_left_bottom_sizer.AddSpacer(10)
        self.top_left_bottom_sizer.Add(wx.StaticBitmap(self, -1, elite_bmp))

        self.top_right_sizer.Add(wx.StaticBitmap(self, -1, building_bmp))
        self.top_right_sizer.AddSpacer(5)
        self.top_right_sizer.Add(wx.StaticBitmap(self, -1, protection_bmp))

        self.top_left_sizer.Add(self.top_left_bottom_sizer)
        self.top_sizer.Add(self.top_left_sizer)
        self.top_sizer.AddSpacer(10)
        self.top_sizer.Add(self.top_right_sizer)

        # display all parameters

        params = [(
            'life', '{0}/{1}'.format(int(self.unit['parameters']['life']), int(self.unit['parameters']['max_life']))),
            ('shield', str(int(self.unit['parameters']['shield']))),
            ('shoot_dist', str(int(self.unit[
                                   'parameters']['shoot_dist']))),
            ('walk_dist', str(int(self.unit[
                                  'parameters']['walk_dist']))),
            ('attack', '{0}-{1}'.format(int(self.unit['parameters'][
                                            'attack_min']), int(self.unit['parameters']['attack_max']))),
            ('delay', str(int(self.unit['delay'])))
        ]

        self.params_sizer = wx.FlexGridSizer(3, 5)
        self.params_images = {}
        self.params_value = {}

        spacer = True

        for param, value in params:
            image = 'icon_' + param
            self.params_images[image] = wx.StaticBitmap(
                self, wx.ID_ANY, all_graphics[image])
            self.params_value[param] = wx.StaticText(self, -1, value)
            self.params_value[param].SetFont(fonts['parameter'])

            self.params_sizer.Add(self.params_images[image])
            self.params_sizer.Add(self.params_value[param], 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

            if spacer:
                self.params_sizer.AddSpacer(20)

            spacer = not spacer

        # Make e list of all actions (scrolled): the action_panel
        self.action_panel = scrolled.ScrolledPanel(self, -1, size=(145, 50))

        self.action_sizer = wx.BoxSizer(wx.VERTICAL)
        self.all_actions = {}

        self.collected_actions = {'upgrade': {}, 'shop': {}, 'equipment': {}}
        # Create each action (a button and a description)
        for name, action in self.unit['parameters']['actions'].items():
            if action['category'] != 'standard':
                self.collected_actions[action['category']][name] = action

            else:
                hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
                self.all_actions[name] = wx.BitmapButton(
                    self.action_panel, -1, self.all_graphics['button_action'],
                    name=name, size=(20, 20), style = wx.BORDER_NONE)
                self.all_actions[name].Bind(wx.EVT_BUTTON, self.on_unit_action)

                label = name + ' '
                if action['price'] > 0:
                    label += ', ' + str(int(action['price'])) + '$'

                if action['delay'] > 0:
                    label += ', wait ' + str(int(action['delay']))

                if action['num_uses'] != -1:
                    label += ', ' + str(action['num_uses']) + 'x'

                action_label = wx.StaticText(self.action_panel, -1, label)
                action_label.SetFont(fonts['small'])

                hor_sizer.Add(self.all_actions[name])
                hor_sizer.Add(action_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
                self.action_sizer.Add(hor_sizer)

        # shortcuts (action categories)
        self.shortcuts = {}
        shortcut_sizer = wx.BoxSizer(wx.HORIZONTAL)

        for sh in ['upgrade', 'shop', 'equipment']:
            if len(self.collected_actions[sh]) > 0:
                img = 'button_' + sh
                self.shortcuts[sh] = wx.BitmapButton(
                    self.action_panel, -1, self.all_graphics[img],
                    style=wx.BORDER_NONE, name=sh)
                self.shortcuts[sh].Bind(wx.EVT_BUTTON, self.on_action_category)

                shortcut_sizer.Add(self.shortcuts[sh], 0, wx.LEFT, 10)

        self.action_sizer.AddSpacer(10)
        self.action_sizer.Add(shortcut_sizer)

        self.action_panel.SetSizer(self.action_sizer)

        self.action_panel.SetupScrolling(False, True)

        self.main_sizer.Add(self.top_sizer)
        self.main_sizer.AddSpacer(15)
        self.main_sizer.Add(self.params_sizer)
        self.main_sizer.AddSpacer(15)
        self.main_sizer.Add(self.action_panel)

        self.SetSizer(self.main_sizer)

    def on_action_category(self, evt):
        category = evt.GetEventObject().GetName()
        actions = self.collected_actions[category]
        dlg = ActionCategory(self, category, actions, self.all_graphics)
        success = dlg.ShowModal()
        if success:
            action = dlg.selected_action
            new_event = ActionEvent(
                INITIATE_ACTION, self.GetId(), action_type='unit_action',
                o_id=self.g_id, u_id=self.u_id, action_name=action)
            dlg.Destroy()
            self.GetEventHandler().ProcessEvent(new_event)

    def update_parameters(self, new_obj):
        params = [(
            'life', '{0}/{1}'.format(int(new_obj['parameters']['life']), int(new_obj['parameters']['max_life']))),
            ('shield', str(int(new_obj['parameters']['shield']))),
            ('shoot_dist', str(int(new_obj[
                                   'parameters']['shoot_dist']))),
            ('walk_dist', str(int(new_obj['parameters']['walk_dist']))),
            ('attack', '{0}-{1}'.format(int(new_obj['parameters'][
                                            'attack_min']), int(new_obj['parameters']['attack_max']))),
            ('delay', str(int(new_obj['delay'])))
        ]

        for param, value in params:
            self.params_value[param].SetLabel(value)

    def on_unit_action(self, evt):
        action_name = evt.GetEventObject().GetName()
        # Create an Action Event with all the necessary parameters
        new_event = ActionEvent(
            INITIATE_ACTION, self.GetId(), action_type='unit_action',
            o_id=self.g_id, u_id=self.u_id, action_name=action_name)

        # Process Event (handled in Main Frame)
        self.GetEventHandler().ProcessEvent(new_event)


class ObjSummary(wx.Panel):

    '''Displayed as image: unit (incl health), elite, building, protected,

    as text: delay left, life, attack, dist shoot, dist walk, age, total_damage
    actions as buttons in separate scrolled panel'''

    def __init__(self, parent, o_id, obj, all_graphics, is_building=False):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.all_graphics = all_graphics
        self.o_id = o_id
        self.obj = obj
        self.is_building = is_building
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        if self.is_building:
            start = 'building_'
        else:
            start = 'transporter_'

        try:
            unit_bmp = all_graphics[start + str(obj['parameters']['id'])]
        except KeyError:
            unit_bmp = all_graphics['unknown']

        try:
            elite = 'rank_' + str(int(obj['parameters']['elite']))
            elite_bmp = all_graphics[elite]
        except KeyError:
            elite_bmp = all_graphics['rank_8']

        # Sizers
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_left_bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)

        name = obj['parameters']['name'] + ' ' + obj['name']
        self.top_left_sizer.Add(wx.StaticText(self, -1, name))
        self.top_left_sizer.AddSpacer(10)

        self.top_left_bottom_sizer.Add(wx.StaticBitmap(self, -1, unit_bmp))
        self.top_left_bottom_sizer.AddSpacer(10)
        self.top_left_bottom_sizer.Add(wx.StaticBitmap(self, -1, elite_bmp))

        self.top_left_sizer.Add(self.top_left_bottom_sizer)
        self.top_sizer.Add(self.top_left_sizer)

        # Parse Units
        current_in = obj['current']
        if self.is_building:
            if len(current_in) > 0:
                groups = {}
                for g_id, u_id in current_in:
                    try:
                        groups[g_id].append(u_id)
                    except KeyError:
                        groups[g_id] = [u_id]

                current = 'Groups:'
                for g_id, u_ids in groups.items():
                    current += ' ' + str(g_id) + ': ' + str(len(u_ids)) + 'x'
            else:
                current = 'No units in building'
        else:
            if len(current_in) > 0:
                cur = [str(c) for c in current_in]
                groups = ', '.join(cur)
                current = 'Groups: ' + groups
            else:
                current = 'No groups transported'

        self.current = wx.StaticText(self, -1, current)

        # display all parameters
        try:
            wd = str(int(obj['parameters']['walk_dist']))
        except KeyError:
            wd = '0'

        params = [(
            'life', '{0}/{1}'.format(int(obj['parameters']['life']), int(obj['parameters']['max_life']))),
            ('shield', str(int(obj['parameters']['shield']))),
            ('shoot_dist', str(int(obj['parameters']['shoot_dist']))),
            ('walk_dist', wd),
            ('attack', '{0}-{1}'.format(int(obj['parameters'][
                                            'attack_min']), int(obj['parameters']['attack_max']))),
            ('delay', str(int(obj['delay']))),
            ('capacity', '{0}/{1}'.format(
             len(current_in), int(obj['parameters']['capacity'])))
        ]

        self.params_sizer = wx.FlexGridSizer(3, 5)
        self.params_images = {}
        self.params_value = {}

        spacer = True

        for param, value in params:
            image = 'icon_' + param
            self.params_images[image] = wx.StaticBitmap(
                self, wx.ID_ANY, all_graphics[image])

            self.params_value[param] = wx.StaticText(self, -1,  str(value))
            self.params_value[param].SetFont(fonts['parameter'])

            self.params_sizer.Add(self.params_images[image])
            self.params_sizer.Add(self.params_value[param], 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 3)

            if spacer:
                self.params_sizer.AddSpacer(15)

            spacer = not spacer

        # The enter parameter (two bitmaps)
        self.params_images['icon_enter'] = wx.StaticBitmap(
            self, -1, all_graphics['icon_enter'])

        if self.is_building:
            u_type = obj['parameters']['enter']
        else:
            u_type = obj['parameters']['transports']

        self.params_value['enter'] = wx.StaticBitmap(
            self, -1, all_graphics['icon_group_' + u_type + 's'])

        self.params_sizer.Add(self.params_images['icon_enter'])
        self.params_sizer.Add(self.params_value['enter'], 0, wx.LEFT, 5)

        # Make e list of all actions (scrolled): the action_panel
        self.action_panel = scrolled.ScrolledPanel(self, -1, size=(145, 100))

        self.action_sizer = wx.BoxSizer(wx.VERTICAL)
        self.all_actions = {}

        self.collected_actions = {'upgrade': {}, 'shop': {}, 'equipment': {}}
        # Create each action (a button and a description)
        for name, action in self.obj['parameters']['actions'].items():
            if action['category'] != 'standard':
                self.collected_actions[action['category']][name] = action

            else:
                hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
                self.all_actions[name] = wx.BitmapButton(
                    self.action_panel, -1, self.all_graphics['button_action'],
                    name=name, size=(20, 20), style = wx.BORDER_NONE)
                self.all_actions[name].Bind(wx.EVT_BUTTON, self.on_unit_action)

                label = name + ' '
                if action['price'] > 0:
                    label += ', ' + str(int(action['price'])) + '$'

                if action['delay'] > 0:
                    label += ', wait ' + str(int(action['delay']))

                if action['num_uses'] != -1:
                    label += ', ' + str(action['num_uses']) + 'x'

                action_label = wx.StaticText(self.action_panel, -1, label)
                action_label.SetFont(fonts['small'])

                hor_sizer.Add(self.all_actions[name])
                hor_sizer.Add(action_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
                self.action_sizer.Add(hor_sizer)

        # shortcuts (action categories)
        self.shortcuts = {}
        shortcut_sizer = wx.BoxSizer(wx.HORIZONTAL)

        for sh in ['upgrade', 'shop', 'equipment']:
            if len(self.collected_actions[sh]) > 0:
                img = 'button_' + sh
                self.shortcuts[sh] = wx.BitmapButton(
                    self.action_panel, -1, self.all_graphics[img],
                    style=wx.BORDER_NONE, name=sh)
                self.shortcuts[sh].Bind(wx.EVT_BUTTON, self.on_action_category)

                shortcut_sizer.Add(self.shortcuts[sh], 0, wx.LEFT, 10)

        self.action_sizer.AddSpacer(10)
        self.action_sizer.Add(shortcut_sizer)

        self.action_panel.SetSizer(self.action_sizer)

        self.action_panel.SetupScrolling(False, True)

        self.main_sizer.Add(self.top_sizer)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.current)
        self.main_sizer.AddSpacer(10)
        self.main_sizer.Add(self.params_sizer)
        self.main_sizer.AddSpacer(15)
        self.main_sizer.Add(self.action_panel)

        self.SetSizer(self.main_sizer)

        self.Show(True)

    def on_action_category(self, evt):
        category = evt.GetEventObject().GetName()
        actions = self.collected_actions[category]
        dlg = ActionCategory(self, category, actions, self.all_graphics)
        success = dlg.ShowModal()
        if success:
            action = dlg.selected_action
            new_event = ActionEvent(
                INITIATE_ACTION, self.GetId(), action_type='unit_action',
                o_id=self.o_id, action_name=action)
            dlg.Destroy()
            self.GetEventHandler().ProcessEvent(new_event)

    def update_parameters(self, new_obj):
        try:
            wd = str(int(new_obj['parameters']['walk_dist']))
        except KeyError:
            wd = '0'

        current = new_obj['current']
        if self.is_building:
            if len(current) > 0:
                groups = {}
                for g_id, u_id in current:
                    try:
                        groups[g_id].append(u_id)
                    except KeyError:
                        groups[g_id] = [u_id]

                current = 'Groups, Units:'
                for g_id, u_ids in groups.items():
                    current += ' ' + str(g_id) + ': '
                    for u_id in u_ids:
                        current += str(u_id) + ','
            else:
                current = 'No units in building'
        else:
            if len(current) > 0:
                groups = ''
                for g in current:
                    groups += str(g) + ', '
                current = 'Groups: ' + groups
            else:
                current = 'No groups transported'

        self.current.SetLabel(current)

        params = [(
            'life', '{0}/{1}'.format(int(new_obj['parameters']['life']), int(new_obj['parameters']['max_life']))),
            ('shield', str(int(new_obj['parameters']['shield']))),
            ('shoot_dist', str(int(new_obj[
                                   'parameters']['shoot_dist']))),
            ('walk_dist', wd),
            ('attack', '{0}-{1}'.format(int(new_obj['parameters'][
                                            'attack_min']), int(new_obj['parameters']['attack_max']))),
            ('delay', str(int(new_obj['delay'])))
        ]

        for param, value in params:
            self.params_value[param].SetLabel(value)

    def on_unit_action(self, evt):
        action_name = evt.GetEventObject().GetName()
        # Create an Action Event with all the necessary parameters
        new_event = ActionEvent(
            INITIATE_ACTION, self.GetId(), action_type='unit_action',
            o_id=self.o_id, action_name=action_name)

        # Process Event (handled in Main Frame)
        self.GetEventHandler().ProcessEvent(new_event)


class ActionPanel(wx.Panel):

    def __init__(self, parent, all_graphics):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, size=(825, 50))
        self.all_graphics = all_graphics

        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.actions = {}

        all_actions = [  # The name and the corresponding image
            ('move', 'action_move'),
            ('fight', 'action_fight'),
            ('load_transporter', 'action_transport'),
            ('unload_group', 'action_exit_transporter'),
            ('protect', 'action_protect'),
            ('unprotect', 'action_unprotect'),
            ('enter_building', 'action_enter_building'),
            ('exit_building', 'action_exit_building'),
            ('move_units', 'action_mix_group'),
            ('rename', 'action_rename')]

        for action, image in all_actions:
            bmp_normal = all_graphics[image]
            bmp_inactive = all_graphics[image + '_delay']

            self.actions[action] = wx.BitmapButton(
                self, bitmap=bmp_normal, size=(45, 45),
                style = wx.BORDER_NONE, name = action)
            self.actions[action].Bind(wx.EVT_BUTTON, self.on_action)
            # self.actions[action] = buttons.GenBitmapButton(self, bitmap =
            # bmp_normal|)
            self.actions[action].SetBitmapDisabled(bmp_inactive)
            self.actions[action].SetBackgroundColour(colors[1])

            self.main_sizer.Add(self.actions[action])
            self.main_sizer.AddSpacer(7)

            self.actions[action].Enable(False)

        self.SetSizer(self.main_sizer)

    def update_allowed_actions(self, allowed_actions):
        for action in self.actions.keys():
            if action in allowed_actions:
                self.actions[action].Enable(True)
            else:
                self.actions[action].Enable(False)

        # self.FitInside()

    def on_action(self, evt):

        obj = evt.GetEventObject()
        action_type = obj.GetName()

        # create and process ActionEvent (handled in Main Frame)
        new_event = ActionEvent(
            INITIATE_ACTION, self.GetId(), action_type=action_type)
        self.GetEventHandler().ProcessEvent(new_event)


class IconPanel(scrolled.ScrolledPanel):

    def __init__(self, parent, all_graphics):
        scrolled.ScrolledPanel.__init__(self, parent, -1, size=(1000, 300))
        self.all_graphics = all_graphics

        self.icon_sizer = wx.GridSizer(10, 6)
        self.relayout = False

        self.SetSizer(self.icon_sizer)
        self.SetupScrolling(False, True)
        # self.SetAutoLayout(1)
        self.displayed = {}

    def update_displayed(self, game_obj):
        self.game_obj = game_obj
        displayed_left = self.displayed.keys()
        added = False
        for b_id, building in game_obj['buildings'].items():
            try:
                self.displayed[b_id].update_icon(building)
                displayed_left.remove(b_id)
            # building is not displayed yet
            except KeyError:
                # create the icon
                self.displayed[b_id] = Icon(
                    self, 'building', b_id, building, self.all_graphics)
                # handle the selection button
                self.Bind(wx.EVT_BUTTON, self.icon_selected)
                self.icon_sizer.Add(self.displayed[b_id], 0, wx.ALL, 5)
                added = True

        for t_id, transporter in game_obj['transporter'].items():
            try:
                self.displayed[t_id].update_icon(transporter)
                displayed_left.remove(t_id)
            # building is not displayed yet
            except KeyError:
                # create the icon
                self.displayed[t_id] = Icon(
                    self, 'transporter', t_id, transporter, self.all_graphics)
                # handle the selection button
                self.Bind(wx.EVT_BUTTON, self.icon_selected)
                self.icon_sizer.Add(self.displayed[t_id], 0, wx.ALL, 5)
                added = True

        for g_id, group in game_obj['groups'].items():

            # group average needs to be calculated here, to use only one Icon
            total_walk = 0
            total_attack = 0
            total_life = 0

            for unit in group['units'].values():
                # Calculate total attack and total life
                if unit['parameters']['walk_dist'] < total_walk:
                    total_walk = unit['parameters']['walk_dist']

                # attack is median of min and max attack
                attack = (unit['parameters']['attack_min']
                          + unit['parameters']['attack_max']) / 2
                total_attack += attack

                total_life += unit['parameters']['life']

            total_attack /= len(group['units'].keys())

            group['parameters'] = {}
            group['parameters']['walk_dist'] = total_walk
            group['parameters']['attack_min'] = total_attack
            group['parameters']['attack_max'] = total_attack
            group['parameters']['life'] = total_life

            try:
                self.displayed[g_id].update_icon(group)
                displayed_left.remove(g_id)
            # building is not displayed yet
            except KeyError:
                # create the icon
                self.displayed[g_id] = Icon(
                    self, 'group', g_id, group, self.all_graphics)
                # handle the selection button
                self.Bind(wx.EVT_BUTTON, self.icon_selected)
                self.icon_sizer.Add(self.displayed[g_id], 0, wx.ALL, 5)
                added = True

        for o_id in displayed_left:
            self.displayed[o_id].Destroy()
            del self.displayed[o_id]

        if added:
            if len(self.displayed.keys()) == 19:
                # IMPLEMENT: Find which condition to renew frame...
                self.FitInside()
            else:
                self.FitInside()

    def shortcut_used(self, o_id):
        for id in self.displayed.keys():
            if id == o_id:
                self.displayed[id].select_btn.SetValue(True)
            else:
                self.displayed[id].select_btn.SetValue(False)

    def icon_selected(self, e):
        e.Skip()


class Icon(wx.Panel):

    def __init__(self, parent, object_type, o_id, obj, all_graphics):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.all_graphics = all_graphics

        self.o_id = o_id

        # self.top_level_sizer.Add(self.title)
        # self.top_level_sizer.AddSpacer(5)
        if object_type == 'building':
            ind = str(obj['parameters']['id'])
            img = 'building_' + ind
        elif object_type == 'transporter':
            ind = str(obj['parameters']['id'])
            img = 'transporter_' + ind
        elif object_type == 'group':
            u_ids = []
            u_types = []
            for unit in obj['units'].values():
                u_id = unit['parameters']['id']
                u_type = unit['parameters']['unit_type']
                if u_id not in u_ids:
                    u_ids.append(u_id)
                if u_type not in u_types:
                    u_types.append(u_type)

            if len(u_ids) == 1:
                img = 'unit_' + str(u_ids[0])
            else:
                if len(u_types) == 1:
                    img = 'group_' + u_types[0] + 's'
                else:
                    img = 'group_mixed'

        try:
            bmp_normal = all_graphics[img]
            bmp_selected = all_graphics[img + '_mo']
        except KeyError:
            bmp_normal = all_graphics['unknown']
            bmp_selected = all_graphics['unknown_mo']

        self.select_btn = buttons.GenBitmapToggleButton(
            self, bitmap=bmp_normal, size=(45, 45), name=str(o_id), style = wx.BORDER_NONE)
        self.select_btn.SetBitmapSelected(bmp_selected)
        self.Bind(wx.EVT_BUTTON, self.icon_selected, self.select_btn)

        self.delay_bar = pg.PyGauge(self, -1, size=(80, 10), style=wx.GA_HORIZONTAL)
        self.delay_bar.SetBackgroundColour(colors[1])
        self.delay_bar.SetBorderColor(colors[0])
        self.delay_bar.SetBarColor(colors[2])

        self.name = wx.StaticText(self, wx.ID_ANY, '')
        self.number = wx.StaticText(self, wx.ID_ANY, '')
        self.attack_text = wx.StaticText(self, wx.ID_ANY, '')
        self.life_text = wx.StaticText(self, wx.ID_ANY, '')
        self.walk_text = wx.StaticText(self, wx.ID_ANY, '')

        self.number.SetFont(fonts['large_number'])
        self.name.SetFont(fonts['small'])
        self.attack_text.SetFont(fonts['parameter'])
        self.life_text.SetFont(fonts['parameter'])
        self.walk_text.SetFont(fonts['parameter'])

        self.DoLayout()
        self.update_icon(obj)

    def DoLayout(self):

        self.SetBackgroundColour(colors[1])

        top_level_sizer = wx.BoxSizer(wx.VERTICAL)
        top_level_sizer.SetMinSize((150, 80))

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_level_sizer.Add(main_sizer, 0, wx.TOP, 5)

        left_sizer = wx.BoxSizer(wx.VERTICAL)

        hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hor_sizer.Add(self.number, 0, wx.LEFT, 5)
        hor_sizer.Add(self.select_btn, 0, wx.LEFT, 5)

        left_sizer.Add(hor_sizer)
        left_sizer.AddSpacer(2)
        left_sizer.Add(self.name, 0, wx.LEFT, 5)
        left_sizer.AddSpacer(2)
        left_sizer.Add(self.delay_bar, 0, wx.LEFT, 5)

        main_sizer.Add(left_sizer, 0, wx.RIGHT, 10)

        parameter_sizer = wx.BoxSizer(wx.VERTICAL)
        attack_sizer = wx.BoxSizer(wx.HORIZONTAL)
        life_sizer = wx.BoxSizer(wx.HORIZONTAL)
        walk_sizer = wx.BoxSizer(wx.HORIZONTAL)

        attack_sizer.Add(
            wx.StaticBitmap(self, wx.ID_ANY, self.all_graphics['icon_attack']))
        attack_sizer.Add(self.attack_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 3)

        life_sizer.Add(
            wx.StaticBitmap(self, wx.ID_ANY, self.all_graphics['icon_life']))
        life_sizer.Add(self.life_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 3)

        walk_sizer.Add(wx.StaticBitmap(self, wx.ID_ANY, self.all_graphics['icon_walk_dist']))
        walk_sizer.Add(self.walk_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 3)

        parameter_sizer.Add(attack_sizer)
        parameter_sizer.Add(life_sizer, 0, wx.TOP, 5)
        parameter_sizer.Add(walk_sizer, 0, wx.TOP, 5)

        main_sizer.Add(parameter_sizer)
        self.SetSizer(top_level_sizer)

    def update_icon(self, obj):

        use_red = False
        if 'units' in obj.keys():
            delay_min = 1000
            delay_max = 0
            life = 0
            attack = 0
            walk_dist = 1000000
            for u in obj['units'].values():
                u_p = u['parameters']
                if u['delay'] > delay_max:
                    delay_max = u['delay']
                if u['delay'] < delay_min:
                    delay_min = u['delay']
                if u_p['walk_dist'] < walk_dist and obj['transporter'] == -1 and u['building'] == -1:
                    walk_dist = u_p['walk_dist']

                attack += round((u_p['attack_min']+u_p['attack_max'])/float(2))
                life += u_p['life']
                if u_p['life'] < 20:
                    use_red = True
        else:
            o_p = obj['parameters']
            delay_min = obj['delay']
            delay_max = obj['delay']
            life = o_p['life']

            if life < 20:
                use_red = True

            attack = round((o_p['attack_min']+o_p['attack_max'])/float(2))
            try:
                walk_dist = o_p['walk_dist']
            except KeyError:
                # Buildings do not have a walk_dist
                walk_dist = 0

        if delay_max > 20:
            delay_max = 20

        val = int(round(float(delay_max)/20*100))
        self.delay_bar.SetValue(val)

        self.attack_text.SetLabel(str(int(attack)))
        self.life_text.SetLabel(str(int(life)))

        if use_red:
            self.life_text.SetForegroundColour(wx.RED)
        else:
            self.life_text.SetForegroundColour(colors[0])

        self.walk_text.SetLabel(str(int(walk_dist)))

        self.number.SetLabel(str(self.o_id))
        self.name.SetLabel(obj['name'])

        self.delay_bar.Refresh()

    def icon_selected(self, e):
        e.Skip()


class MessageBoard(wx.Panel):

    def __init__(self, parent, size_display, all_graphics):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.size_display = size_display
        self.all_graphics = all_graphics
        self.current_id = 0
        self.messages = {}
        self.msg_btn = {}
        self.top_level_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_level_sizer.AddSpacer(10)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.AddSpacer(10)
        self.scroll_panel = scrolled.ScrolledPanel(self, -1, size=(310, 290))
        self.message_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_panel.SetSizer(self.message_sizer)
        self.scroll_panel.SetupScrolling(False, True)

        self.main_sizer.Add(self.scroll_panel, 0, wx.EXPAND)
        self.top_level_sizer.Add(self.main_sizer)
        self.SetSizer(self.top_level_sizer)
        self.Layout()

    def add_message(self, message):
        self.messages[self.current_id] = message
        self.current_id += 1

        msg_disp = sorted(self.messages.keys())

        while len(msg_disp) > self.size_display:
            msg_disp.pop(0)

        msg_disp = reversed(msg_disp)

        self.message_sizer.Clear(True)
        # for btn_id in self.msg_btn.keys():
        #    self.msg_btn[btn_id].Destroy()

        self.msg_btn = {}
        for message_id in msg_disp:
            self.msg_btn[message_id] = wx.BitmapButton(
                self.scroll_panel, -1, self.all_graphics['button_message'], size=(20, 20), style = wx.BORDER_NONE)
            self.Bind(wx.EVT_BUTTON, lambda event, m=message_id:
                      self.message_click(event, m), self.msg_btn[message_id])

            hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
            hor_sizer.Add(self.msg_btn[message_id])
            hor_sizer.AddSpacer(10)
            hor_sizer.Add(wx.StaticText(
                self.scroll_panel, -1, self.messages[message_id]['title']), 0, wx.ALIGN_CENTER_VERTICAL)

            self.message_sizer.Add(hor_sizer)
            self.message_sizer.AddSpacer(5)

        self.scroll_panel.FitInside()
        # self.scroll_panel.Layout()

        # Display popup if requested
        if message['popup']:
            wx.MessageBox(message['message'], message['title'],
                          wx.OK | wx.ICON_INFORMATION)

    def message_click(self, e, message_id):
        # Display clicked message in new popup (running in a seperate thread
        msg = self.messages[message_id]
        wx.MessageBox(
            msg['message'], msg['title'], wx.OK | wx.ICON_INFORMATION)


class PlayCard(wx.Dialog):

    def __init__(self, parent, size_display, all_graphics, connection):
        wx.Dialog.__init__(self, parent, 'Play a Card')
        self.size_display = size_display
        self.all_graphics = all_graphics
        self.connection = connection
        self.cards = {}
        self.card_btn = {}
        self.enemy_ids = {}
        self.own_ids = {}
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.scroll_panel = scrolled.ScrolledPanel(self, -1, size=(175, 200))
        self.card_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_panel.SetSizer(self.card_sizer)
        self.scroll_panel.SetupScrolling(False, True)

        self.main_sizer.Add(self.scroll_panel, 0, wx.EXPAND)

        self.SetSizer(self.main_sizer)
        self.Layout()

    def update_cards(self, cards):
        self.cards = cards

        self.card_sizer.Clear()
        for btn_id in self.card_btn.keys():
            self.card_btn[btn_id].Destroy()

        self.card_btn = {}
        if self.cards:
            for c_id, card in self.cards.items():
                self.card_btn[c_id] = wx.Button(self.scroll_panel, wx.ID_ANY, label=card['title'] +
                                                '\n' + card['description'], size=(150, 60))
                self.Bind(wx.EVT_BUTTON, lambda event, m=c_id:
                          self.card_click(event, m), self.card_btn[c_id])
                self.card_sizer.Add(self.card_btn[c_id])

        self.scroll_panel.FitInside()
        # self.scroll_panel.Layout()
        # self.Layout()

    def update_ids(self, enemy_ids, own_ids):
        self.enemy_ids = enemy_ids
        self.own_ids = own_ids

    def card_click(self, e, card_id):
        card = self.cards[card_id]
        self.EndModal(True)

    def card_click_old(self, e, card_id):
        card = self.cards[card_id]
        # check if card needs to ask for enemy, enemy_ids and own_ids
        enemy = False
        enemy_ids = False
        own_ids = False
        selection = {'enemy': False, 'enemy_selection': False,
                     'own_selection': False}

        for ac in card['actions']:
            if ac['target'] == 'enemy':
                enemy = True
                if ac['type'] != 'new' and ac['level'] != 'player':
                    if ac['num_units'] != 'all':
                        enemy_ids = True

            elif ac['target'] == 'own' and ac['level'] != 'player':
                if ac['type'] != 'new':
                    if ac['num_units'] != 'all':
                        own_ids = True

        # Ask for targets for enemy
        if enemy:
            if len(self.enemy_ids.keys()) > 0:
                dial = wx.SingleChoiceDialog(
                    None, 'Choose your enemy...', 'Choose Enemy', self.enemy_ids.keys())
                res = dial.ShowModal()
                if res != wx.ID_OK:
                    dial.Destroy()
                    return

                selection['enemy'] = dial.GetStringSelection()
                dial.Destroy()

                if selection['enemy'] and enemy_ids:
                    if self.enemy_ids:
                        groups = [str(
                            group) for group in self.enemy_ids[selection['enemy']]]
                        dial = wx.MultiChoiceDialog(
                            None, 'Choose enemy groups...', 'Choose Groups', groups)
                        res = dial.ShowModal()
                        if res != wx.ID_OK:
                            dial.Destroy()
                            return

                        sel_groups = dial.GetSelections()
                        selection['enemy_selection'] = [
                            int(groups[group]) for group in sel_groups]
                        dial.Destroy()

        if own_ids:
            if self.own_ids:
                groups = [str(group) for group in self.own_ids]
                dial = wx.MultiChoiceDialog(
                    None, 'Choose your own groups', 'Choose Groups', groups)
                res = dial.ShowModal()
                if res != wx.ID_OK:
                    dial.Destroy()
                    return
                sel_groups = dial.GetSelections()
                selection['own_selection'] = [int(
                    groups[group]) for group in sel_groups]
                dial.Destroy()

        # Display clicked message in new popup (running in a seperate thread)
        if selection['own_selection'] or selection['enemy_selection'] or selection['enemy'] or not (enemy and enemy_ids and own_ids):
            self.connection.Send({'action': 'play_card',
                                 'card_id': card_id, 'selection': selection})
