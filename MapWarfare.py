import wx
import os
from threading import Thread
import socket
from PodSixNet.Connection import connection, ConnectionListener

class MapWarfareScanner(ConnectionListener):
	def __init__(self, adress, port):
		self.players = False

		# Get all ips on the net
		self.Connect((adress, port))
		for i in range(10):
			connection.Pump()
			time.sleep(0.01)

		return self.players

	def Network_pong(self, data):
		self.players = data['players']


def run_server():
	os.system('python MapWarfareServer.py')

class MapWarfare(wx.Dialog):
	def __init__(self):
		'''
			
		'''
		
		# Initialize Superclass
		wx.Dialog.__init__(self, None, -1, 'MapWarfare Splash Screen', size = (1024, 768))
		self.init_layout()

	def init_layout(self):
		# Title
		title = 'MapWarfare Splash Screen'

		# Add a few buttons

		btns = [
			wx.Button(self, -1, 'Create Game'),
			wx.Button(self, -1, 'Refresh'),
			wx.Button(self, -1, 'Join Game'),
			wx.Button(self, -1, 'Close')
		]

		calls = [self.create_game, self.refresh_games, self.close, self.close]

		main_sizer = wx.BoxSizer(wx.VERTICAL)
		main_sizer.Add(wx.StaticText(self, -1, title), 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 15)

		for i, b in enumerate(btns):
			b.Bind(wx.EVT_BUTTON, calls[i])
			main_sizer.Add(b, 0, wx.ALIGN_RIGHT)

		# Setup & show
		self.SetSizer(main_sizer)
		self.Layout()
		self.Show()

	def create_game(self, evt):
		thread = Thread(target = run_server)
		thread.start()

	def refresh_games(self, evt):
		adress = 'localhost'
		port = 31425

		# adresses = socket.gethostbyname(socket.gethostname())

		adresses = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]][:1]
		print type(adresses), adresses

	def close(self, evt):
		if self.IsModal():			
			self.EndModal(True)
		else:
			self.Close()

if __name__ == '__main__':
	app = wx.App(
		# redirect=True,filename="log.txt"
	)
	MapWarfare()
	app.MainLoop()
	print 'here'