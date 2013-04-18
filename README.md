MapWarfare
==========

##### Standard View

![Standard View](/screenshots/1.png "Standard View")




##### Shop View

![Shop View](/screenshots/2.png "Shop View")




##### Getting started:

1. Download and Install: [Python 2.7.x](http://python.org/download/) & [wxPython 2.8 (py27)](http://wxpython.org/download.php)

2. Clone repository or download as .zip (see top of page)

-------------------

3. Start the Server by double-clicking MapWarfareServer.py

4. Load a configuration from file (.army)
	(make changes if you're feeling bold ==> This will most likely produce an error now or later...).

5. Start the Server ==> Your IP will be shown (clients can connect to this IP)

--------------------

6. Start the Client (MapWarfareClient.py)

7. Enter the Server IP and Port (just hit enter if you are running the Server on your machine).

8. Choose a name and starting sector 
	(Sector has to be available/defined in configuration file, usually 1-10 is not a bad guess)

--------------------

Some more tips:

Change the server speed on-the-go & use the Play/Pause button in the User Interface
Below 0.1s/tick is not recomended as the UI will not be able to keep up.

Toggle Fullscreen using F11 and use the number keys to directly select groups
Save current selection with CTRL + Number
F1-F10 are shortcuts to the actions: F1 = Move, F2 = Attack, ...


There is an enemy included ('punch_me'), so you have someone to battle...
Lines 67 to 74 in engine.py define what units each player starts with.
You can also remove punch_me there (prefix line with # to comment it).