import wx
import wx.wizard as wiz


def makePageTitle(wizPg, title):
    sizer = wx.BoxSizer(wx.VERTICAL)
    wizPg.SetSizer(sizer)
    title = wx.StaticText(wizPg, -1, title)
    title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
    sizer.Add(title, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
    sizer.Add(wx.StaticLine(wizPg, -1), 0, wx.EXPAND | wx.ALL, 4)
    return sizer


class DistancePage(wiz.WizardPageSimple):

    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = makePageTitle(self, 'Distance between groups')
        self.sizer.Add(wx.StaticText(self, -1, """
            Enter the distance between the units in cm."""))
        self.distance = wx.TextCtrl(self, -1, '5', size=(250, -1))
        self.sizer.Add(self.distance)

    def get_value(self):
        # I know; WTF...
        return {'distance': int(round(float(self.distance.GetValue())))}


class OwnPage(wiz.WizardPageSimple):

    def __init__(self, parent, groups, transporter, buildings, sector=False, selection=False):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = makePageTitle(self, 'Select Own Targets')
        self.sizer.Add(wx.StaticText(self, -1, """
            Which IDs/Units are you targeting?"""))
        self.select_groups = wx.ListBox(self, -1, style=wx.LB_MULTIPLE)

        if selection:
            all_items = selection
        else:
            all_items = {}

            for g_id, group in groups.items():
                for u_id, unit in groups[g_id]['units'].items():
                    all_items[str(g_id) + ': ' + unit['name']] = (g_id, u_id)
            for o_id, obj in transporter.items():
                all_items['Transporter: ' + str(o_id)] = tuple([o_id])
            for o_id, obj in buildings.items():
                all_items['Building: ' + str(o_id)] = tuple([o_id])

        self.all_items = all_items

        self.select_groups.AppendItems(sorted(all_items.keys()))

        self.sizer.Add(self.select_groups)

    def get_value(self):
        adresses = []
        indici = self.select_groups.GetSelections()
        for index in indici:
            adress = self.all_items[self.select_groups.GetString(index)]
            adresses.append(adress)
        return {'own_adresses': adresses}


class TransporterPage(wiz.WizardPageSimple):

    def __init__(self, parent, transporter):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = makePageTitle(self, 'Select Transporter')
        self.sizer.Add(wx.StaticText(self, -1, """
            Which transporter?"""))
        self.select_groups = wx.ListBox(self, -1)
        groups = [str(group) for group in transporter.keys()]
        self.select_groups.AppendItems(groups)

        self.sizer.Add(self.select_groups)

    def get_value(self):
        return {'transporter': int(self.select_groups.GetStringSelection())}


class SectorPage(wiz.WizardPageSimple):

    def __init__(self, parent, sectors, current_sector, walk_dist=0, selected_ids=False):
        wiz.WizardPageSimple.__init__(self, parent)

        self.selected_ids = selected_ids

        self.walk_dist = wx.StaticText(self, -1, str(walk_dist))
        self.walk_dist.SetFont(wx.Font(25, wx.SWISS, wx.NORMAL, wx.NORMAL))

        self.select_groups = wx.ListBox(self, -1)

        all_sectors = [str(sect) for sect in sectors.keys()]

        current_index = all_sectors.index(str(current_sector))
        self.select_groups.AppendItems(all_sectors)
        self.select_groups.SetSelection(current_index)

        self.DoLayout()

    def DoLayout(self):
        title = 'Move Units'

        if self.selected_ids:
            title += ': ' + ', '.join(map(lambda x: str(x), self.selected_ids))

        self.sizer = makePageTitle(self, title)

        main = wx.BoxSizer(wx.HORIZONTAL)
        left = wx.BoxSizer(wx.VERTICAL)
        right = wx.BoxSizer(wx.VERTICAL)

        left.Add(wx.StaticText(self, -1, "Walk Distance:"), 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        left.Add(self.walk_dist, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)

        right.Add(wx.StaticText(self, -1, "New sector?"), 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        right.Add(self.select_groups, 0, wx.ALIGN_CENTER_HORIZONTAL)

        main.Add(left, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)
        main.Add(right, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)

        self.sizer.Add(main)

    def get_value(self):
        return {'sector': int(self.select_groups.GetStringSelection())}


class BuildingPage(wiz.WizardPageSimple):

    def __init__(self, parent, buildings):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = makePageTitle(self, 'Select Building')
        self.sizer.Add(wx.StaticText(self, -1, """
            Which building?"""))
        self.select_groups = wx.ListBox(self, -1)
        groups = [str(group) for group in buildings.keys()]
        self.select_groups.AppendItems(groups)

        self.sizer.Add(self.select_groups)

    def get_value(self):
        return {'building': int(self.select_groups.GetStringSelection())}


class EnemyPage(wiz.WizardPageSimple):

    def __init__(self, parent, enemy_groups, select_ids=False, sector=False, selected_ids = False):
        '''Select enemy.
        Optional:
        choose ids of selected enemy,
        limit ids to specific sector
        '''

        wiz.WizardPageSimple.__init__(self, parent)
        self.sector = sector
        self.enemy_groups = enemy_groups
        self.select_ids = select_ids
        self.selected_ids = selected_ids
        self.select_enemy = wx.ComboBox(self, choices=enemy_groups.keys(), style=wx.CB_READONLY,)

        if select_ids:
            self.select_groups = wx.ListBox(self, -1, style=wx.LB_MULTIPLE, size = (50, 200))
            self.select_enemy.Bind(wx.EVT_COMBOBOX, self.enemy_selected)

        self.DoLayout()

    def DoLayout(self):
        title = 'Select Enemy'
        if self.selected_ids:
            title += ' for ' + ', '.join(map(lambda x: str(x), self.selected_ids))

        self.sizer = makePageTitle(self, title)
        self.sizer.Add(wx.StaticText(self, -1, """
            Choose the enemy player you are targeting."""))
        self.sizer.Add(self.select_enemy)

        if hasattr(self, 'select_groups'):
            self.sizer.Add(wx.StaticText(self, -1, """
                Which IDs are you targeting?"""))
            self.sizer.Add(self.select_groups)

    def enemy_selected(self, evt):
        enemy = self.select_enemy.GetStringSelection()
        all_ids = []
        for o_id, cur_sector in self.enemy_groups[enemy].items():
            if self.sector != False:
                if cur_sector == self.sector:
                    all_ids.append(str(o_id))
            else:
                all_ids.append(str(o_id))

        self.select_groups.Clear()
        self.select_groups.AppendItems(all_ids)

    def get_value(self):
        enemy = {'enemy_player': self.select_enemy.GetStringSelection()}
        if self.select_ids:
            ids = []
            indici = self.select_groups.GetSelections()
            for index in indici:
                ids.append(int(self.select_groups.GetString(index)))

            enemy['enemy_ids'] = ids

        return enemy


class ActionWizard(wiz.Wizard):

    def __init__(self, evt, selected_ids, enemy_groups, sectors,
                 groups, transporter, buildings, cards, connection):

        self.connection = connection
        self.sectors = sectors
        self.selected_ids = selected_ids
        self.evt = evt
        self.enemy_groups = enemy_groups
        self.transporter = transporter
        self.groups = groups
        self.buildings = buildings
        self.cards = cards
        wiz.Wizard.__init__(self, None, -1)

        def show_wizard(pages):

            self.FitToPage(pages[0])

            # Use the convenience Chain function to connect the pages
            if len(pages) > 1:
                for ind in range(len(pages) - 1):
                    wiz.WizardPageSimple_Chain(pages[ind], pages[ind + 1])

            self.GetPageAreaSizer().Add(pages[0])
            if self.RunWizard(pages[0]):
                parameters = {}
                for page in pages:
                    ret_param = page.get_value()
                    for param, value in ret_param.items():
                        parameters[param] = value

                return parameters

            return False

        action_type = self.evt.action_type
        pages = []
        sel = {'groups': [], 'buildings': [], 'transporter': []}

        for ind in self.selected_ids:
            if ind in self.groups.keys():
                current_sector = self.groups[ind]['sector']
                sel['groups'].append(ind)
            elif ind in self.transporter.keys():
                current_sector = self.transporter[ind]['sector']
                sel['transporter'].append(ind)
            elif ind in self.buildings.keys():
                current_sector = self.buildings[ind]['sector']
                sel['buildings'].append(ind)

        if action_type == 'fight':
            pages.append(EnemyPage(self, self.enemy_groups, select_ids=True, selected_ids = self.selected_ids))
            pages.append(DistancePage(self))
            params = show_wizard(pages)

            if params:
                enemies = {params['enemy_player']: params['enemy_ids']}
                data = {'action': 'fight', 'own_units': self.selected_ids,
                        'enemies': enemies, 'distance': params['distance']}
                self.connection.Send(data)

        elif action_type == 'move':
            # It sucks to be doing this again...
            wd = []
            for indx in self.selected_ids:
                if indx in self.groups.keys():
                    for u_id, u in self.groups[indx]['units'].items():
                        wd.append(u['parameters']['walk_dist'])
                elif indx in self.transporter.keys():
                    wd.append(self.transporter[indx]['parameters']['walk_dist'])
                elif indx in self.buildings.keys():
                    wd.append(0)

            walk_dist = min(wd)
            
            pages.append(SectorPage(self, self.sectors, current_sector, walk_dist, self.selected_ids))
            params = show_wizard(pages)
            if params:
                self.connection.Send(
                    {'action': 'move_into_sector', 'ids': self.selected_ids,
                     'sector': params['sector']})

        elif action_type == 'load_transporter' and len(sel['transporter']) == 1 and len(sel['groups']) == 1:
            self.connection.Send(
                {'action': 'load_transporter', 'transporter': sel['transporter'][0],
                 'group': sel['groups'][0]})

        elif action_type == 'enter_building':
            self.connection.Send(
                {'action': 'enter_building', 'building': sel['buildings'][0],
                 'group': sel['groups'][0]})

        elif action_type == 'exit_building':
            self.connection.Send(
                {'action': 'exit_building', 'group': sel['groups'][0]})

        elif action_type == 'unload_group':
            self.connection.Send(
                {'action': 'unload_group', 'group': sel['groups'][0]})

        elif action_type == 'protect':
            self.connection.Send(
                {'action': 'protect_groups', 'groups': self.selected_ids})

        elif action_type == 'unprotect':
            self.connection.Send(
                {'action': 'unprotect_groups', 'groups': self.selected_ids})

        elif action_type == 'play_card':
            # Get actions and check which questions need to be asked:
            c_id = evt.o_id
            card = self.cards[c_id]
            has_enemy_player = False
            has_enemy_ids = False
            has_own_ids = False

            for action in card['actions']:
                if action['target'] == 'enemy':
                    if action['level'] == 'id' and action['num_units'] != 'all':
                        has_enemy_ids = True
                    has_enemy_player = True
                elif action['target'] == 'own':
                    if action['level'] == 'id' and action['num_units'] != 'all':
                        has_own_ids = True

            if has_enemy_player:
                pages.append(EnemyPage(self, self.enemy_groups,
                             select_ids=has_enemy_ids, sector=False))
            if has_own_ids:
                pages.append(OwnPage(self, self.groups,
                             self.transporter, self.buildings, sector=False))

            if pages:
                params = show_wizard(pages)
            else:
                params = False

            selection = {}
            if has_enemy_player:
                selection['enemy'] = params['enemy_player']
            else:
                selection['enemy'] = False

            if has_enemy_ids:
                selection['enemy_selection'] = params['enemy_ids']
            else:
                selection['enemy_selection'] = False

            if has_own_ids:
                selection['own_selection'] = params['own_adresses']
            else:
                selection['own_selection'] = False

            data = {'action': 'play_card', 'card_id': c_id,
                    'selection': selection}

            self.connection.Send(data)

        elif action_type == 'unit_action':
            # Get actions and check which questions need to be asked:
            name = evt.action_name
            o_id = evt.o_id
            building = False
            if evt.u_id != None:
                u_id = evt.u_id
                actions = self.groups[o_id]['units'][u_id][
                    'parameters']['actions'][name]['actions']
            elif o_id in self.transporter.keys():
                u_id = False
                actions = self.transporter[o_id][
                    'parameters']['actions'][name]['actions']
            elif o_id in self.buildings.keys():
                building = True
                u_id = False
                actions = self.buildings[o_id][
                    'parameters']['actions'][name]['actions']

            has_enemy_player = False
            has_enemy_ids = False
            has_own_ids = False

            for action in actions:
                if action['target'] == 'enemy':
                    if action['level'] == 'id' and action['num_units'] != 'all':
                        has_enemy_ids = True
                    has_enemy_player = True
                elif action['target'] == 'own':
                    if action['level'] == 'id' and action['num_units'] != 'all':
                        has_own_ids = True

            if has_enemy_player:
                pages.append(EnemyPage(self, self.enemy_groups,
                             select_ids=has_enemy_ids, sector=False))
            if has_own_ids:
                if building:
                    in_building = {}
                    for oo_id, u_id in self.buildings[o_id]['current']:
                        name = ' '.join([str(oo_id), ': ',
                                        self.groups[oo_id]['units'][u_id]['name']])
                        in_building[name] = (oo_id, u_id)
                    selection = in_building
                else:
                    selection = False
                pages.append(OwnPage(self, self.groups, self.transporter,
                             self.buildings, sector=False, selection=selection))

            if pages:
                params = show_wizard(pages)
            else:
                params = False

            selection = {}
            if has_enemy_player:
                selection['enemy'] = params['enemy_player']
            else:
                selection['enemy'] = False

            if has_enemy_ids:
                selection['enemy_selection'] = params['enemy_ids']
            else:
                selection['enemy_selection'] = False

            if building:
                in_building = self.buildings[o_id]['current']

            if has_own_ids:
                selection['own_selection'] = params['own_adresses']
            else:
                # I think this is mostly used for actions on 'self'
                selection['own_selection'] = False  # [tuple([o_id])]

            if evt.u_id != None:
                u_id = evt.u_id
            else:
                u_id = False

            data = {
                'action': 'unit_action', 'sector': current_sector, 'action_name': evt.action_name,
                'o_id': evt.o_id, 'u_id': u_id, 'selection': selection}

            self.connection.Send(data)
