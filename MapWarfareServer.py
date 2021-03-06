from time import sleep, asctime, time
from weakref import WeakKeyDictionary
import wx, socket, os
from configuration_helper import ConfigurationHelper

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

import engine

class ServerUI(wx.Frame):

    '''This is the user interface to manage the server. it allows you to
    start and pause the game (the ticks) and set the duration of one tick.
    You can also see which players are connected.'''

    def __init__(self, current_tick=25):
        super(ServerUI, self).__init__(None, -1, 'Uster Wars Server', size=(400, 300))

        self.load_flag = False
        self.save_flag = False
        self.duration_flag = False
        self.play_flag = False

        self.play_btn = wx.ToggleButton(self, -1, 'Run Ticks', size=(80, 100))
        self.play_btn.Bind(wx.EVT_TOGGLEBUTTON, self.play_pause)

        self.slider = wx.Slider(self, 600, current_tick, 3, 600, (30, 60), (250, -1),
                                wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.slider.Bind(wx.EVT_SLIDER, self.on_slide)

        self.manual_entry = wx.TextCtrl(self, -1, str(current_tick))
        self.change_duration_btn = wx.Button(self, -1, 'Change Duration')
        self.change_duration_btn.Bind(wx.EVT_BUTTON, self.change_duration)

        self.save_btn = wx.Button(self, -1, 'Save Game')
        self.load_btn = wx.Button(self, -1, 'Load Game')
        self.save_btn.Bind(wx.EVT_BUTTON, self.OnSave)
        self.load_btn.Bind(wx.EVT_BUTTON, self.OnLoad)

        self.DoLayout()

    def DoLayout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        play_sizer = wx.BoxSizer(wx.HORIZONTAL)
        duration_sizer = wx.BoxSizer(wx.VERTICAL)
        hor_sizer = wx.BoxSizer(wx.HORIZONTAL)

        main_sizer.Add(wx.StaticText(self, -1, 'Uster Wars Server'), 0, wx.BOTTOM, 10)

        play_sizer.Add(self.play_btn, 0, wx.RIGHT, 10)

        duration_sizer.Add(wx.StaticText(self, -1, 'Tick Duration (s):'))
        duration_sizer.Add(self.slider)

        hor_sizer.Add(self.manual_entry, 0, wx.RIGHT, 10)
        hor_sizer.Add(self.change_duration_btn)

        duration_sizer.Add(hor_sizer)
        play_sizer.Add(duration_sizer)
        main_sizer.Add(play_sizer)

        main_sizer.Add(self.save_btn, 0, wx.TOP|wx.ALIGN_CENTER_HORIZONTAL, 8)
        main_sizer.Add(self.load_btn, 0, wx.TOP|wx.ALIGN_CENTER_HORIZONTAL, 8)
        self.SetSizer(main_sizer)

    def play_pause(self, evt):
        play = self.play_btn.GetValue()
        if play:
            self.play_flag = 1
        else:
            self.play_flag = -1

    def change_duration(self, evt):
        self.duration_flag = float(self.manual_entry.GetValue())

    def on_slide(self, evt):
        self.manual_entry.SetValue(str(self.slider.GetValue()))

    def OnSave(self, evt):
        dlg = wx.FileDialog(self, 'Choose a filename', '', '', '*.game', wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            self.save_flag = os.path.join(dirname, filename)

    def OnLoad(self, evt):
        dlg = wx.FileDialog(self, 'Choose a file', '', '', '*.game', wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            self.load_flag = os.path.join(dirname, filename)


class ClientChannel(Channel):

    def __init__(self, *args, **kwargs):
        self.nickname = "anonymous"
        Channel.__init__(self, *args, **kwargs)

    def Close(self):
        self._server.del_player(self)

    #
    # Network specific callbacks ###
    #
    def Network_ping(self, data):
        self._server.pong(self)

    def Network_rename_id(self, data):
        self._server.rename_id(self, data)

    def Network_move_into_sector(self, data):
        self._server.move_into_sector(self, data)

    def Network_buy_group(self, data):
        self._server.buy_group(self, data)

    def Network_buy_building(self, data):
        self._server.buy_building(self, data)

    def Network_fight(self, data):
        self._server.fight(self, data)

    def Network_register(self, data):
        self.nickname = data['nickname']
        self._server.register_player(self, data['nickname'], data['sector'])

    def Network_load_transporter(self, data):
        self._server.load_transporter(self, data)

    def Network_unload_group(self, data):
        self._server.unload_group(self, data)

    def Network_protect_groups(self, data):
        self._server.protect_groups(self, data)

    def Network_unprotect_groups(self, data):
        self._server.unprotect_groups(self, data)

    def Network_move_units(self, data):
        self._server.move_units(self, data)

    def Network_buy_transporter(self, data):
        self._server.buy_transporter(self, data)

    def Network_buy_card(self, data):
        self._server.buy_card(self, data)

    def Network_play_card(self, data):
        self._server.play_card(self, data)

    def Network_unit_action(self, data):
        self._server.unit_action(self, data)

    def Network_enter_building(self, data):
        self._server.enter_building(self, data)

    def Network_exit_building(self, data):
        self._server.exit_building(self, data)

    def Network_run_ticks(self, data):
        self._server.run_ticks(data['status'])


class MapWarfareServer(Server):
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.players = WeakKeyDictionary()

        self.last_tick = 0

        self.game_paused = True

        # Use configuration helper to get game parameters
        game_parameters = self.configuration_helper()

        self.tick_duration = game_parameters['engine_parameters']['tick_duration']

        self.game = engine.MapWarfare(game_parameters)
        # Create a wxPython app
        self.wx_app = wx.App(
            #redirect=True,filename="server_crash_log.txt"
        )
        self.init_user_interface()

    def configuration_helper(self):
        conf_app = wx.App(
            #redirect=True,filename="helper_crash_log.txt"
        )

        dial = ConfigurationHelper()

        start = dial.ShowModal()

        if start:
            return dial.game_parameters
        else:
            return {}

    def init_user_interface(self):
        # Load all images as bitmaps
        self.frame = ServerUI(self.tick_duration)
        self.frame.Show()
        self.wx_app.Yield()

    def pong(self, channel):
        # Pong back all player names
        channel.Send({
            'action': 'pong',
            'players': self.game.players.keys()
            })
        

    def Connected(self, channel, addr):
        self.AddPlayer(channel)

    def AddPlayer(self, player):
        print str(player.addr) + ' connected: ' + asctime()[11:19]
        self.players[player] = True

    def register_player(self, player, nickname, sector):
        msg_stack = self.game.new_player(nickname, sector)

        pl = self.game.players[nickname]

        player.Send({"action": "update_ui",
                     "groups": pl['groups'],
                     'transporter': pl['transporter'],
                     'buildings': pl['buildings'],
                     'cards': pl['cards'],
                     'game_parameters': self.game.game_parameters,
                     'status': self.get_status(nickname),
                     'enemy_groups': self.game.get_all_enemy_groups(nickname),
                     'sectors': dict(self.game.sectors),
                     'play': not self.game_paused
                     })

        if type(msg_stack) == dict:
            self.send_msg_stack(msg_stack)

        print 'Registered ' + player.nickname + ': ' + asctime()[11:19]

    def get_status(self, nickname):
        pl = self.game.players[nickname]
        sectors = [sec for sec, pla in self.game.sectors.items() if pla == nickname]
        
        diff = self.game.get_victory_difference(nickname)
        status = {'account': pl['account'], 'sectors': sectors,
                  'name': nickname, 'diff': diff, 'ticks': self.game.ticks}

        return status

    def del_player(self, player):
        print "Deleting Player" + str(player.addr) + ' ' + asctime()
        del self.players[player]

    def update_groups_status(self, player, update_selection=False):
        nickname = str(player.nickname)

        pl = self.game.players[nickname]

        player.Send(
            {"action": "update_ui", 
            "groups": pl['groups'], 'transporter': pl['transporter'], 'buildings': pl['buildings'],
             'cards': False, 
             'game_parameters': False, 
             'enemy_groups': self.game.get_all_enemy_groups(nickname), 
             'status': self.get_status(nickname), 
             'sectors': False,
             'update_selection': update_selection})

    def update_player_ui(self, player, update_selection=False):
        nickname = str(player.nickname)
        try:
            pl = self.game.players[nickname]
        except KeyError:
            return

        player.Send({"action": "update_ui", "groups": pl['groups'],
                     'transporter': pl['transporter'], 'buildings': pl['buildings'],
                     'game_parameters': False, 
                     'enemy_groups': self.game.get_all_enemy_groups(nickname),
                     'cards': pl['cards'],
                     'status': self.get_status(nickname), 
                     'sectors': self.game.sectors,
                     'update_selection': update_selection})

    def update_sectors_all(self):

        for player in self.players:
            nickname = str(player.nickname)

            player.Send({"action": "update_ui", "groups": False, 'game_parameters': False, 'enemy_groups': False,
                         'status': self.get_status(nickname), 'transporter': False, 'buildings': False, 'sectors': self.game.sectors,
                         'cards': False})

    def update_enemy_groups_all(self):

        for player in self.players:
            nickname = str(player.nickname)
            player.Send({"action": "update_ui", "groups": False, 'transporter': False, 'buildings': False,
                         'cards': False, 'game_parameters': False, 
                         'enemy_groups': self.game.get_all_enemy_groups(nickname),
                         'status': False, 'sectors': False})

    def send_msg_stack(self, msg_stack):
        inv_players = [p for p in msg_stack.keys() if p not in ('all', 'others')]
        for player, msg in msg_stack.items():
            if player not in ('all', 'others'):
                # Add time to message
                msg['message'] += '\n\nSent at ' + asctime()[11:19]
                # Search player and send message
                for p in self.players:
                    if p.nickname == player:
                        p.Send({"action": "message", "message": msg})
                        break

        # Send message to all other players or all players in general
        for p in self.players:
            if p.nickname not in inv_players:
                try:
                    msg = msg_stack['others']
                    msg['message'] += '\n\nSent at ' + asctime()[11:19]
                    p.Send({"action": "message", "message": msg})
                except KeyError:
                    pass
            try:
                msg = msg_stack['all']
                msg['message'] += '\n\nSent at ' + asctime()[11:19]
                p.Send({"action": "message", "message": msg})
            except KeyError:
                pass

    def buy_group(self, player, data):
        print player.nickname + ' buys group: ' + asctime()[11:19]
        msg_stack = self.game.new_group(player.nickname, data['units'], data['sector'], data['name'])

        self.update_groups_status(player)
        self.update_enemy_groups_all()
        self.send_msg_stack(msg_stack)

    def fight(self, player, data):
        msg_stack = self.game.fight({str(player.nickname): data['own_units']}, data['enemies'], data['distance'])
        inv_players = [str(player.nickname)] + data['enemies'].keys()
        for player in self.players:
            if player.nickname in inv_players:
                self.update_player_ui(player, True)

        self.send_msg_stack(msg_stack)

        print 'Fight between: ' + str(inv_players) + ': ' + asctime()[11:19]
        self.update_enemy_groups_all()

    def protect_groups(self, player, data):
        print player.nickname + ' protects groups: ' + asctime()[11:19]
        msg_stack = self.game.protect_groups(player.nickname, data['groups'])
        self.update_groups_status(player, True)
        self.send_msg_stack(msg_stack)

    def unprotect_groups(self, player, data):
        print player.nickname + ' unprotects groups: ' + asctime()[11:19]
        msg_stack = self.game.unprotect_groups(player.nickname, data['groups'])
        self.update_groups_status(player, True)
        self.send_msg_stack(msg_stack)

    def enter_building(self, player, data):
        print player.nickname + ' enters building: ' + asctime()[11:19]
        msg_stack = self.game.enter_building(player.nickname, data['group'], data['building'])
        self.update_groups_status(player, True)
        self.send_msg_stack(msg_stack)

    def exit_building(self, player, data):
        print player.nickname + ' exits buidling: ' + asctime()[11:19]
        msg_stack = self.game.exit_building(player.nickname, data['group'])
        self.update_groups_status(player, True)
        self.send_msg_stack(msg_stack)

    def load_transporter(self, player, data):
        print player.nickname + ' loads transporter: ' + asctime()[11:19]
        msg_stack = self.game.load_transporter(player.nickname, data['group'], data['transporter'])
        self.update_groups_status(player, True)
        self.send_msg_stack(msg_stack)

    def unload_group(self, player, data):
        print player.nickname + ' unloads group: ' + asctime()[11:19]
        msg_stack = self.game.unload_group(player.nickname, data['group'])
        self.update_groups_status(player, True)
        self.send_msg_stack(msg_stack)

    def buy_transporter(self, player, data):
        print player.nickname + ' buys transporter: ' + asctime()[11:19]
        msg_stack = self.game.new_transporter(player.nickname, data['transporter'], data['sector'], data['name'])
        self.update_groups_status(player)
        self.update_enemy_groups_all()
        self.send_msg_stack(msg_stack)

    def buy_card(self, player, data):
        print player.nickname + ' buys card: ' + asctime()[11:19]
        msg_stack = self.game.new_card(player.nickname, data['amount'])
        self.update_player_ui(player)
        self.send_msg_stack(msg_stack)

    def move_units(self, player, data):
        print player.nickname + ' changes groups: ' + asctime()[11:19]
        msg_stack = self.game.move_units(player.nickname, data['changes'], data['new_name'])
        self.update_groups_status(player)
        self.send_msg_stack(msg_stack)

    def move_into_sector(self, player, data):
        print player.nickname + ' moves: ' + asctime()[11:19]
        for o_id in data['ids']:
            msg_stack = self.game.move_into_sector(player.nickname, o_id, data['sector'])

        self.update_groups_status(player, True)
        # self.send_msg_stack(msg_stack)

    def rename_id(self, player, data):
        print player.nickname + ' renames id: ' + asctime()[11:19]
        # Directly access attribute and change name
        self.game.rename_id(player.nickname, data['id'], data['name'])
        self.update_groups_status(player, False)
        # self.send_msg_stack(msg_stack)

    def unit_action(self, player, data):
        print player.nickname + ' unit action: ' + asctime()[11:19]
        if data['sector']:
            sector = data['sector']
        else:
            sector = False

        msg_stack = self.game.perform_unit_action(player.nickname, data['action_name'], data['o_id'],
                                                  data['u_id'], data['selection'], sector=sector)
        self.update_groups_status(player, True)
        self.send_msg_stack(msg_stack)

    def play_card(self, player, data):
        print player.nickname + ' plays card: ' + asctime()[11:19]
        msg_stack = self.game.play_card(player.nickname, data['card_id'], data['selection'], False)
        self.update_player_ui(player)
        if data['selection']['enemy']:
            for p in self.players:
                if p.nickname == data['selection']['enemy']:
                    self.update_player_ui(p)
                    break

        self.send_msg_stack(msg_stack)

    def run_ticks(self, status):
        print 'Run ticks, ' + str(status) + ': ' + asctime()[11:19]
        self.game_paused = not status
        self.frame.play_btn.SetValue(status)
        for player in self.players:
            player.Send({"action": "update_ui", "groups": False, 'game_parameters': False, 'enemy_groups': False,
                         'status': False, 'transporter': False, 'buildings': False, 'sectors': False,
                         'play': status, 'cards': False})

    def on_tick(self):
        msg_stack = self.game.on_tick()
        for player in self.players:
            self.update_player_ui(player)

        self.send_msg_stack(msg_stack)


    def Launch(self):
        '''The server loop'''

        print 'Map Warfare Server started!'
        print 'Server Adress:', socket.gethostbyname(socket.gethostname()), ', Port:', self.addr[1]
        
        while True:
            # Perform all requests
            self.Pump()
            # check if next tick is due
            if not self.game_paused:
                if time() >= self.last_tick + self.tick_duration:
                    self.last_tick = time()
                    # initiate a tick in the game engine
                    self.on_tick()

            self.wx_app.Yield()

            # check if duration was changed
            if self.frame.duration_flag:
                self.tick_duration = self.frame.duration_flag
                self.frame.duration_flag = False

            # check if save or load was triggered:
            if self.frame.load_flag:
                self.game.load_game(self.frame.load_flag)
                self.frame.load_flag = False

            if self.frame.save_flag:
                self.game.save_game(self.frame.save_flag)
                self.frame.save_flag = False

            # check if play pause was changed
            pl = self.frame.play_flag
            if pl:
                if pl == 1:
                    self.run_ticks(True)

                elif pl == -1:
                    self.run_ticks(False)

                self.frame.play_flag = False

            sleep(0.005)

s = MapWarfareServer(localaddr=('0.0.0.0', 31425))  # 0.0.0.0
s.Launch()
