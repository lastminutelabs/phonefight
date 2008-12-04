# Phone Fight v0.3

# a sword-fighting game for the n95 hacked up in 12 hours at Over The
# Air 2008 (overtheair.org) by lastminute.com labs

# http://labs.lastminute.com/phonefight

# Copyright lastminute.com (C) 2008

# You may copy, modify and redistribute the program under the terms of
# the GNU General Public Licence, version 2. You will find a copy of
# the licence in the GPL file.

import appuifw
import audio
import axyz
import e32
import math
import random
import sensor
import socket
import sys
import traceback
import graphics

# Misty is noce to remove the screensave but we're OK without it
try:
    __import__('misty')
except:
    pass


class UI:
    
    FRAME_INTERVAL=0.1
    
    def __init__(self):
        
        # Initialize some properties
        self.needs_refresh=True
        
        # Create the canvas
        self.backgroundImage=None
        appuifw.app.orientation='portrait'
        appuifw.app.screen='large'
        self.canvas=appuifw.Canvas ( redraw_callback=self.handle_redraw, event_callback=self.handle_event )
        appuifw.app.body=self.canvas
        
        # Blank the background of the canvas
        w,h=self.canvas.size
        bgcolor=graphics.Image.new((w, h))
        bgcolor.clear((0,0,0))
        self.canvas.blit(bgcolor)
        
        # Load the images
        self.backgroundImage=self.load_image('e:\\Python\\fight_bg.png')
        self.hitImage=self.load_image('e:\\Python\\hit_1.gif')
        
        # Make sure that the background gets draw immediately
        self.handle_redraw(None)
        
        # Start a refresh timer
        self.timer=e32.Ao_timer()
        self.timer.after(UI.FRAME_INTERVAL, self.update_ui)
        
    def __del__(self):
        self.timer.cancel()
        
    # Loads the specified image or returns a 1x1 blank image in case of an error
    def load_image(self, src):
        try:
            return graphics.Image.open(src)
        except:
            return graphics.Image.new((1,1))
    
    def update_ui(self):
        if (self.needs_refresh):
            self.handle_redraw(None)
        self.timer.after(UI.FRAME_INTERVAL, self.update_ui)
        
    def handle_event(self, event):
        self.handle_redraw(None)
        
    def handle_redraw(self, rect=None):
        if self.backgroundImage:
            try:
                self.canvas.blit(self.backgroundImage)
            except:
                pass
            self.needs_refresh=False



# everything is in a try block for safety reasons. stand back!
try:
    # this hardcoding is because bt_discover doesn't alway work
    # edit this if necessary
    PHONES = [("Athos", "00:18:32:E7:1B:60"),
              ("Porthos", "00:1E:3A:25:46:8B"),
              ("Aramis", "00:1F:03:AE:64:0C"),
              ("Labs", "00:1F:00:AE:54:0C")]

    PHONE_NAMES = [unicode(n) for n, a in PHONES]
    PHONE_ADDRESSES = [a for n, a in PHONES]

    # how to advertise our service
    BT_SERVICE_NAME = u"lastminute.com labs PhoneFight v0"

    # that bluetooth phonefight protocol in full
    HORIZONTAL_ATTACK_MESSAGE, VERTICAL_ATTACK_MESSAGE, VICTORY_MESSAGE = 'H', 'V', 'W' 

    # how many magnitude/orientation samples to keep
    HISTORY_SIZE = 16

    # how healthy is our player to begin with        
    INITIAL_HEALTH = 10

    # can't attack again within this many seconds
    QUIET_INTERVAL = 0.3

    # wake up and read socket every this many seconds
    TICK_INTERVAL = 0.04

    # need acceleration magnitude of this much to cause an attack
    ATTACK_THRESHOLD = 100

    # modes of play
    CHAMPION_MODE, CHALLENGER_MODE, PRACTICE_MODE = 0, 1, 2 

    # event types
    (INCOMING_HORIZONTAL_ATTACK_EVENT, INCOMING_VERTICAL_ATTACK_EVENT,
     OUTGOING_HORIZONTAL_ATTACK_EVENT, OUTGOING_VERTICAL_ATTACK_EVENT,
     VICTORY_EVENT) = range(5)

    # useful for debugging
    ORIENTATION_AS_STRING = {sensor.orientation.LEFT: "left",
                             sensor.orientation.RIGHT: "right",
                             sensor.orientation.TOP: "top",
                             sensor.orientation.BOTTOM: "bottom"}

    def init_sound(path):
        s = audio.Sound.open(path)
        s.set_volume(8)
        return s

    START_SOUND = init_sound("e:\\sounds\phonefight\start.wav")

    CHING_SOUNDS = [init_sound("e:\\sounds\phonefight\ching1.wav"),
                    init_sound("e:\\sounds\phonefight\ching2.wav"),
                    init_sound("e:\\sounds\phonefight\ching3.wav"),
                    init_sound("e:\\sounds\phonefight\ching4.wav"),
                    init_sound("e:\\sounds\phonefight\ching5.wav")]

    HIT_SOUND = init_sound("e:\\sounds\phonefight\hit.wav")
    #VICTORY_SOUND = init_sound("e:\\sounds\phonefight\victory.wav")
    
    WHOOSH_SOUNDS = [init_sound("e:\\sounds\phonefight\whoosh1.wav"),
                     init_sound("e:\\sounds\phonefight\whoosh2.wav"),
                     init_sound("e:\\sounds\phonefight\whoosh3.wav"),
                     init_sound("e:\\sounds\phonefight\whoosh4.wav"),
                     init_sound("e:\\sounds\phonefight\whoosh5.wav"),
                     init_sound("e:\\sounds\phonefight\whoosh6.wav")]

    DEATH_SOUND = init_sound("e:\\sounds\phonefight\death.wav")

    # this is missing in python 2.2
    def zeros(n): return [0 for i in range(n)]
    
    def one_of(a):
        return a[random.randint(0,len(a) - 1)]

    class Fight(object):

        def __init__(self, play_mode, sock):
            self.play_mode = play_mode
            self.sock = sock
            
            self.orientation = sensor.orientation.TOP
            self.silent = False
            self.won = False
            self.elapsed_time = 0.0
            self.last_attack = 0.0
            self.health = INITIAL_HEALTH
            #self.magnitude_history = zeros(HISTORY_SIZE)
            #self.moving_average_magnitude = 0.0
            self.orientation_history = zeros(HISTORY_SIZE)
            self.index = 0
            self.game_over = False
            self.quitting = False

            appuifw.app.exit_key_handler = self.quit
            appuifw.app.menu = [(u"Sound on", self.sound_on),
                                (u"Sound off", self.sound_off),
                                (u"Exit", self.quit)]

            self.timer = e32.Ao_timer()

            self.event = None
            self.eventlock = e32.Ao_lock()
            
            axyz.connect(self.new_accel_data)
            
            sensor_type = sensor.sensors()['RotSensor']
            self.rotation_sensor = sensor.Sensor(sensor_type['id'],
                                                 sensor_type['category'])
            self.rotation_sensor.set_event_filter(sensor.RotEventFilter())
            self.rotation_sensor.connect(self.new_rotation_data)

            self.tick()

        def sound_on(self):
            print "sound on"
            self.silent = False;

        def sound_off(self):
            print "sound off"
            self.silent = True;

        def play(self):
            self.play_sound(START_SOUND)

            while not self.game_over:
                
                # Stop the screensaver coming on (if we have the misty module present)
                if globals().__contains__('misty'):
                    misty.reset_inactivity_time()
                
                self.eventlock.wait()
                if self.event == INCOMING_HORIZONTAL_ATTACK_EVENT:
                    self.defend(self.event)
                elif self.event == INCOMING_VERTICAL_ATTACK_EVENT:
                    self.defend(self.event)
                elif self.event == OUTGOING_HORIZONTAL_ATTACK_EVENT:
                    self.attack(self.event)
                elif self.event == OUTGOING_VERTICAL_ATTACK_EVENT:
                    self.attack(self.event)
                elif self.event == VICTORY_EVENT:
                    self.victory()
                self.event = None
                e32.ao_yield() #?

            self.timer.cancel()
            axyz.disconnect()
            self.rotation_sensor.disconnect()

            return (self.won, self.quitting)
            
        def quit(self):
            self.game_over = True
            self.quitting = True            
            self.eventlock.signal()

        def new_rotation_data(self, orientation):
            print "orientation: %s" % ORIENTATION_AS_STRING[orientation]
            self.orientation = orientation

        def new_accel_data(self, x, y, z):
            magnitude = math.sqrt(x ** 2 + y ** 2 + z ** 2)
            #old_magnitude = self.magnitude_history[self.index]
            #self.moving_average_magnitude += (magnitude - old_magnitude) / HISTORY_SIZE
            #self.magnitude_history[self.index] = magnitude
            self.orientation_history[self.index] = self.orientation
            self.index = (self.index + 1) % HISTORY_SIZE

            now = self.elapsed_time
            if now > (self.last_attack + QUIET_INTERVAL) and magnitude > ATTACK_THRESHOLD:
                # index is now pointing to an event in the recent past
                orientation_then = self.orientation_history[self.index]
                
                if (orientation_then == sensor.orientation.LEFT
                    or orientation_then == sensor.orientation.RIGHT):
                    print "outgoing horizontal attack"
                    self.event = OUTGOING_HORIZONTAL_ATTACK_EVENT
                else:
                    print "outgoing vertical attack"
                    self.event = OUTGOING_VERTICAL_ATTACK_EVENT
                    
                #print "(orientation was %s, last attack %.2f, time now %.2f)" \
                # % (ORIENTATION_AS_STRING[orientation_then], self.last_attack, now)
                self.last_attack = now
                
                self.eventlock.signal()

        def play_sound(self, sound):
            if not self.silent:
                try:
                    sound.stop()
                    sound.play(times=1)
                except:
                    pass

        def defend(self, event):
            # should check for stability?
            if (event == INCOMING_VERTICAL_ATTACK_EVENT):
                print "incoming vertical attack!"
                succeeded = (self.orientation == sensor.orientation.LEFT
                             or self.orientation == sensor.orientation.RIGHT)
            else:
                print "incoming horizontal attack!"
                succeeded = (self.orientation == sensor.orientation.TOP)

            if succeeded:
                print "defence succeeded!"
                self.play_sound(one_of(CHING_SOUNDS))
            else:
                self.health -= 1
                if self.health:
                    print "you're hit, health now %d!" % self.health
                    self.play_sound(HIT_SOUND)
                else:
                    self.dead()

        def dead(self):
            print "you lose!"                
            self.sock.send(VICTORY_MESSAGE)
            self.game_over = True
            self.play_sound(DEATH_SOUND)

        def victory(self):
            print "you win!"                
            #self.play_sound(VICTORY_SOUND)
            self.game_over = True
            self.won = True

        def attack(self, event):
            self.play_sound(one_of(WHOOSH_SOUNDS))
            if self.sock:
                if event == OUTGOING_HORIZONTAL_ATTACK_EVENT:
                    message = HORIZONTAL_ATTACK_MESSAGE
                else:
                    message = VERTICAL_ATTACK_MESSAGE                    
                
                print "sending: %s" % message
                self.sock.send(message)

        def tick(self):
            self.elapsed_time += TICK_INTERVAL
            self.timer.after(TICK_INTERVAL, self.tick)
            
            if self.sock:
                try:
                    message = self.sock.recv(1)
                    if message:
                        event = None
                    
                        if message == HORIZONTAL_ATTACK_MESSAGE:
                            event = INCOMING_HORIZONTAL_ATTACK_EVENT
                        elif message == VERTICAL_ATTACK_MESSAGE:
                            event = INCOMING_VERTICAL_ATTACK_EVENT
                        elif message == VICTORY_MESSAGE:
                            event = VICTORY_EVENT

                        if event is not None:
                            self.event = event
                            self.eventlock.signal()

                except:
                    pass
                

    def server_socket():
        server = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
        channel = socket.bt_rfcomm_get_available_server_channel(server)
        server.bind(("", channel))
        server.listen(1)
        socket.bt_advertise_service(BT_SERVICE_NAME, server, True,
                                    socket.RFCOMM)
        socket.set_security(server, socket.AUTH | socket.AUTHOR)
        print "waiting for client on channel %d ..." % channel
        conn, client_addr = server.accept()
        print "client connected!"
        return conn

    def client_socket():
        conn = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
        print "discovering..."
        try: 
            address, services = socket.bt_discover() # CRASHES!?
        except:
            print "\n".join(traceback.format_exception(*sys.exc_info()))
            appuifw.note(u"Cannot connect. Sorry.", "error")            
            return None
            
        print "found services..."
        if BT_SERVICE_NAME in services:
            print "service available..."
            channel = services[BT_SERVICE_NAME]
            print "got channel..."
            conn.connect((address, channel))
            print "connected to server!"
            return conn
        else:
            print "\n".join(services)            
            appuifw.note(u"Target is not running a Phone Fight server" % BT_SERVICE_NAME,
                         "error")
            return None

    def client_socket_hack():
        conn = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
        phone = appuifw.popup_menu(PHONE_NAMES, u"Phone:")    
        channel = 5 #probably
        try:
            conn.connect((PHONE_ADDRESSES[phone], channel))
            return conn
        except:
            channel = appuifw.query(u"Channel number:", "number")            

        try:
            conn.connect((PHONE_ADDRESSES[phone], channel))
            return conn
        except:
            appuifw.note(u"Cannot connect. Sorry.", "error")            
            return None

    # Initialize the UI
    ui=UI()

    # Start a fight.
    play_mode = appuifw.popup_menu([u"I am the champion",
                                    u"I am the challenger",
                                    u"I need practice"],
                                   u"Select mode of play")

    sock = None
    
    if play_mode == PRACTICE_MODE:
        print "PRACTICE MODE"
        fight = Fight(play_mode, None)
        fight.play()
    else:
        if play_mode == CHAMPION_MODE:
            sock = server_socket()
        elif play_mode == CHALLENGER_MODE:
            discover = not appuifw.popup_menu([u"Yes", u"No"],
                                              u"Discover automatically?")
            if discover:
                sock = client_socket()
            else:
                sock = client_socket_hack()

        if sock:
            sock.setblocking(0)
            playing = True

            while playing:
                print "FIGHT!"            
                fight = Fight(play_mode, sock)
                (won, quitting) = fight.play()

                if quitting:
                    playing = False
                else:
                    if won:
                        result = "won"
                    else:
                        result = "lost"
                    playing = not appuifw.popup_menu([u"Yes", u"No"],
                                                     u"You %s! Play again?" % result)
            sock.close()

    appuifw.app.set_exit()
    
except:
    import appuifw
    import sys
    import traceback
    import e32
    exitlock = e32.Ao_lock()
    def exithandler(): exitlock.signal()
    appuifw.app.exit_key_handler = exithandler
    appuifw.app.menu = [(u"Exit", exithandler)]
    print "\n".join(traceback.format_exception(*sys.exc_info()))
    exitlock.wait()
    appuifw.app.set_exit()
