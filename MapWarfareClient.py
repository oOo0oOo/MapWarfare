from time import sleep
import wx
import ui_elements
import os

from PodSixNet.Connection import connection, ConnectionListener

image_folder = 'images/'


class MapWarfareClient(ConnectionListener):
    def __init__(self, host, port):
        print "Map Warfare client started"
        default = ('localhost', 31425)
        host = raw_input("\nPlease enter server IP:\n(default: %s) " % default[0])
        if not host:
            host = default[0]
        port = raw_input("\nPlease enter port number:\n(default: %s) " % default[1])
        if not port:
            port = default[1]
        else:
            port = int(port)

        self.Connect((host, port))

        nickname = raw_input("\nEnter your nickname:\n")
        sector = int(raw_input("\nStart Sector:\n"))
        connection.Send(
            {"action": "register", "nickname": nickname, 'sector': sector})
        self.wx_app = wx.App(
            redirect=True, filename="client_crash_log.txt"
        )
        self.init_user_interface()

    def init_user_interface(self):
        # Load all images as bitmaps
        all_graphics = {}
        images = os.listdir(image_folder)

        for name in images:
            save_name = name.split('.')[0]
            filepath = image_folder + name
            all_graphics[save_name] = wx.EmptyBitmap(1, 1)
            all_graphics[save_name].LoadFile(filepath, wx.BITMAP_TYPE_ANY)

        self.frame = ui_elements.MainFrame(
            None, 'Map Warfare Client', all_graphics, connection)
        self.frame.Show()
        self.wx_app.Yield()

    def Loop(self):
        connection.Pump()
        self.Pump()
        self.wx_app.Yield()

    #######################################
    ### Network event/message callbacks ###
    #######################################
    def Network_connected(self, data):
        pass

    def Network_error(self, data):
        print 'error:', data['error'][1]
        connection.Close()

    def Network_disconnected(self, data):
        print 'Server disconnected'
        exit()

    def Network_update_ui(self, data):
        self.frame.update_ui(data)

    def Network_message(self, data):
        self.frame.add_message(data['message'])

c = MapWarfareClient('169.254.167.234', 31425)  # 169.254.167.234

while 1:
    c.Loop()
    sleep(0.001)
