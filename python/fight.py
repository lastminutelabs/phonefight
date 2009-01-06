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
import os
import lightblue

# Misty lets us remove the screensave but we're OK without it
try:
    __import__('misty')
except:
    pass


# Everything is in a try block for safety reasons. stand back!
try:
    class UI:
        FRAME_INTERVAL=0.1

        DEFAULT_SOUND_VOLUME=3
        SKINS_PATH="e:\\data\\phonefight\\skins\\"


        def __init__(self):

            # Check to see if skins directory exists
            if not os.path.exists(self.SKINS_PATH):
              print "No skin directory found\n\nYou must download at least one skin to this phone"
              return
            else:
              skins_path = self.SKINS_PATH
              print "checking skins directory for skins..."
              skinsArray = os.listdir(skins_path)
              
              # We need at least one directory in the skins path, so check and proceed if there is one
              
              if len(skinsArray) > 0:
                self.SKINS=[]
                ndx = 0
                
                for skin in skinsArray:
                  print " Found skin: " + skin
                  self.SKINS.append( {
                    'skinName'   : skin,
                    'startSounds': self.__init_sounds(skins_path + skin + "\\sounds\\start\\"),
                    'chingSounds': self.__init_sounds(skins_path + skin + "\\sounds\\defense\\"),
                    'hitSounds':   self.__init_sounds(skins_path + skin + "\\sounds\\hit\\"),
                    'whooshSounds':self.__init_sounds(skins_path + skin + "\\sounds\\attack\\"),
                    'deathSounds': self.__init_sounds(skins_path + skin + "\\sounds\\death\\"),
                    'humSounds':   self.__init_sounds(skins_path + skin + "\\sounds\\hum\\"),
  
  
                    'backgroundImage':self.__load_image(skins_path + skin + '\\images\\fight_bg.png'),
                    'hitImage':       self.__load_image(skins_path + skin + '\\images\\hit_1.png'),
                    'healthImages':   [self.__load_image(skins_path + skin + '\\images\\health_1.png'),
                                    self.__load_image(skins_path  + skin + '\\images\\health_2.png'),
                                    self.__load_image(skins_path  + skin + '\\images\\health_3.png')],
                    'deadImage':      self.__load_image(skins_path + skin + '\\images\\dead.png'),
                    'wonImage':       self.__load_image(skins_path  + skin + '\\images\\won.png')
                                }
                  )
  
                  # Add masks seperately ( is this necessary? )
                  self.SKINS[ndx]['hitImageMask']=         self.__load_mask_for(skins_path  + skin + '\\images\\hit_1_mask.png', self.SKINS[ndx]['hitImage'])
                  self.SKINS[ndx]['healthImageMasks']=    [self.__load_mask_for(skins_path  + skin + '\\images\\health_1_mask.png',self.SKINS[ndx]['healthImages'][0]),
                                                          self.__load_mask_for(skins_path  + skin + '\\images\\health_2_mask.png',self.SKINS[ndx]['healthImages'][1]),
                                                          self.__load_mask_for(skins_path  + skin + '\\images\\health_3_mask.png',self.SKINS[ndx]['healthImages'][2])]
                  self.SKINS[ndx]['deadImageMask']=        self.__load_mask_for(skins_path  + skin + '\\images\\dead_mask.png', self.SKINS[ndx]['deadImage'])
                  self.SKINS[ndx]['wonImageMask']=         self.__load_mask_for(skins_path  + skin + '\\images\\won_mask.png', self.SKINS[ndx]['wonImage'])
  
                  ndx = ndx + 1
              else:
                print "No skins found.  You might need to reinstall, or alternatively put some skins in the e:\data\phonefight\skins directory"


            # Initialize some properties
            self.__hit_counter=0
            self.__health=0
            self.__max_health=0
            self.__playing=False
            self.__silent=False

            self.__skin=self.SKINS[0]
            print "--Skin:" + self.__skin["skinName"]

            self.buffer=None
            self.canvas=None

            # uncomment the return to disable the graphical UI
            return

            # Create the canvas
            appuifw.app.orientation='portrait'
            appuifw.app.screen='large'
            self.canvas=appuifw.Canvas ( redraw_callback=self.__handle_redraw, event_callback=self.__handle_event )
            appuifw.app.body=self.canvas

            # Create an offscreen buffer - draw onto this in the __handle_redraw method and then blit onto the main canvas
            self.buffer=graphics.Image.new(self.canvas.size)

            # Make sure that the background gets draw immediately
            self.__handle_redraw(None)

            # Start a refresh timer
            self.timer=e32.Ao_timer()
            self.timer.after(UI.FRAME_INTERVAL, self.__update_ui)

        def __del__(self):
            self.timer.cancel()

        # Loads the specified image or returns a 1x1 blank image in case of an error
        def __load_image(self, src):
            try:
                img=graphics.Image.open(src)
                return img
            except:
                img=graphics.Image.new((1,1))
                print("Image "+src+" failed to load")
                return img

        def __init_sound(self, path):
            try:
                s = audio.Sound.open(path)
                s.set_volume(self.DEFAULT_SOUND_VOLUME)
                return s
            except:
                print "Warning - sound sample "+path+" not found"
                return None

        def __init_sounds(self, path):
            sounds = []
            try:
               listing = os.listdir(path)
               print "  getting listing from "+path+"."
               return map(lambda f: self.__init_sound((path + f)), listing )
            except:
               print "Warning - error loading sounds from "+path
               return None


        # Using the already loaded image as a guide, it loads a mask from the specifed src and returnes it
        def __load_mask_for(self, mask_src, image):
            try:
                width,height=image.size
                mask=graphics.Image.new((width,height), '1')
                mask.load(mask_src)
                return mask
            except:
                img=graphics.Image.new((1,1), '1')
                print ("Image "+mask_src+" not loaded (as mask)")
                return img

        def __update_ui(self):
            self.__handle_redraw(None)
            self.timer.after(UI.FRAME_INTERVAL, self.__update_ui)

        def __handle_event(self, event):
            #self.__handle_redraw(None)
            pass

        def __handle_redraw(self, rect=None):
            if self.canvas!=None and self.buffer!=None:
                try:
                    # Put the background image in place
                    self.buffer.blit(self.__skin['backgroundImage'])
                except:
                    pass

                try:
                    # Add your health, if we know it yet
                    if self.__max_health>0:
                        if self.__playing:
                            healthImageNumber=int(math.ceil((float(self.__health)/self.__max_health) * (len(self.__skin['healthImages'])-1)))
                            self.buffer.blit(self.__skin['healthImages'][healthImageNumber], mask=self.__skin['healthImageMasks'][healthImageNumber])
                        else:
                            if self.__won:
                                self.buffer.blit(self.__skin['wonImage'], mask=self.__skin['wonImageMask'])
                            else:
                                self.buffer.blit(self.__skin['deadImage'], mask=self.__skin['deadImageMask'])
                except:
                    pass

                try:
                    if self.__hit_counter>0:
                        self.buffer.blit(self.__skin['hitImage'], mask=self.__skin['hitImageMask'])
                        self.__hit_counter-=self.FRAME_INTERVAL
                    else:
                        self.__hit_counter=0
                except:
                    pass

                # We always have _something_ to show on the canvas, even if the previous stuff failed at some point
                self.canvas.blit(self.buffer)

        def __hum_callback(self, prev_state, current_state, error):
            if prev_state == audio.EPlaying and current_state==audio.EOpen:
                self.__stop_hum()
                self.__start_hum()
                
        def __stop_hum(self):
            try:
                self.__skin['humSounds'][0].stop()
            except:
                pass
    
        def __start_hum(self):
            try:
                self.__skin['humSounds'][0].play(times = 600)
            except:
                pass

        def __play_sound(self, sound, hum=False):
            if not self.__silent:
                try:
                    sound.stop()
                    if hum:
                        sound.play(times=1, callback = self.__hum_callback)
                    else:
                        sound.play(times=1)
                except:
                    pass
                
        def invalidate_ui(self):
            # Maybe in the future this will set a flag - currently the ui redraws on each frame anyway
            pass

        def start_anew(self, max_health):
            self.__max_health=max_health
            self.__health=max_health
            self.__playing=True
            self.__play_sound(one_of(self.__skin['startSounds']), True)

        def trigger_hit(self, new_health):
            self.__hit_counter=2
            self.__health=new_health
            self.__play_sound(one_of(self.__skin['hitSounds']), True)
            
        def trigger_defence(self):
            self.__play_sound(one_of(self.__skin['chingSounds']), True)
        
        def trigger_attack_start(self):
            self.__play_sound(one_of(self.__skin['whooshSounds']), True)
        
        def trigger_dead(self):
            self.__play_sound(one_of(self.__skin['deathSounds']), True)

        def won_or_dead(self, have_we_won):
            self.__playing=False
            self.__won=have_we_won
            
        def set_skin(self, new_skin):
            # TODO: make sure that NONE of the humsounds are playing... currently we assume that there's only one
            # .wav file in the /hum/ directory.
            self.__skin['humSounds'][0].stop()
            print " Changing skin: " + new_skin["skinName"] 
            self.__skin=new_skin
            self.__play_sound(one_of(self.__skin['startSounds']), True)     
            
        def setSilent(self, silent):
            self.__silent=silent
            if silent:
                self.__stop_hum()
            else:
                self.__start_hum()


    # this hardcoding is because bt_discover doesn't alway work
    # edit this if necessary
    PHONES = [("Athos", "00:18:32:E7:1B:60"),
              ("Porthos", "00:1E:3A:25:46:8B"),
              ("Aramis", "00:1F:03:AE:64:0C"),
              ("Labs", "00:1F:00:AE:54:0C")]

    PHONE_NAMES = [unicode(n) for n, a in PHONES]
    PHONE_ADDRESSES = [a for n, a in PHONES]

    # How to advertise our service
    BT_SERVICE_NAME = u"lastminute.com labs PhoneFight (lightblue BT layer) v0"
    BT_CHANNEL=5

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



    # this is missing in python 2.2
    def zeros(n): return [0 for i in range(n)]

    def one_of(a):
        return a[random.randint(0,len(a) - 1)]

    class Fight(object):

        def __init__(self, play_mode, sock):
            self.play_mode = play_mode
            self.sock = sock

            self.orientation = sensor.orientation.TOP
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
            appuifw.app.menu = [(unicode(skin["skinName"].title()), self.skin_changer(skin)) for skin in ui.SKINS] + \
                               [(u"Sound on", self.sound_on),
                                (u"Sound off", self.sound_off),
                                (u"Exit", self.quit)]

            # appuifw.app.menu =  appuifw.app.menu + skins_for_menu

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

        # closures in python are wrong if you expect them to reference a snapshot, correct
        # if you expect them to reference a reference.  This is why when we create the menu a
        # few lines above, we end up using a generator function - because we want them to reference
        # a static copy of the values in the ui.SKINS array.  This function below creates the
        # lambda function with a static copy of the skins.
        def skin_changer(self, skin):
            return lambda: ui.set_skin(skin)

        def sound_on(self):
            ui.setSilent(False);

        def sound_off(self):
            ui.setSilent(True);
            
        def play(self):
            ui.start_anew(self.health)

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

            ui.won_or_dead(self.won)

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
                ui.trigger_defence()
            else:
                self.health -= 1
                if self.health:
                    print "you're hit, health now %d!" % self.health
                    ui.trigger_hit(self.health)
                else:
                    self.dead()

        def dead(self):
            print "you lose!"
            self.sock.send(VICTORY_MESSAGE)
            self.game_over = True
            ui.trigger_dead()

        def victory(self):
            print "you win!"
            self.game_over = True
            self.won = True

        def attack(self, event):
            ui.trigger_attack_start()
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
        try:
            server = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
            server.bind(("", BT_CHANNEL))
            server.listen(1)
            socket.set_security(server, socket.AUTH | socket.AUTHOR)
            socket.bt_advertise_service(BT_SERVICE_NAME, server, True, socket.RFCOMM)
            conn, client_addr = server.accept()
            return conn
        except:
            print "Failed to create connection"
            return None
    
    def client_socket():
        device=lightblue.selectdevice()
        
        # Connect to the channel
        try:
            conn = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
            conn.connect((device[0], BT_CHANNEL))
            return conn
        except:
            menu_message(u"Failed to connect to %s"%device[1])
            return None
        
    # Initialize the UI
    play_mode=None
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
            sock = client_socket()

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
