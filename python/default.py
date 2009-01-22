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


def log(text):
    print text
    #handle = open("e:\\python\\phonefight.log","a")
    #handle.write(text + "\n")
    #handle.close()


# Everything is in a try block for safety reasons. stand back!
try:
    class UI:
        __FRAME_INTERVAL=0.1

        __DEFAULT_SOUND_VOLUME=3
        __DATA_PATH="c:\\data\\phonefight\\"
        __SKINS_PATH=__DATA_PATH+"skins\\"

        def __init__(self):
            log("startup of phonefight")
            
            # Initialize some properties
            self.__health=0
            self.__max_health=0
            self.__playing=False
            self.__silent=False
            self.__loading_progress=0.0
            self.__progress_per_skin_section=0.0
            self.__buffer=None
            self.__canvas=None
            self.__timer=None
            
            self.__popup_counter=0
            self.__popup_image=None
            self.__popup_mask=None
            
            self.SKINS=[]
            self.__skin=None
            
            self.__practicing=False
            self.__waiting=False
            
            self.__volume=self.__DEFAULT_SOUND_VOLUME
            
            self.__initialized=False
            self.debug_ui=False # Set to true to load basic skins and not show the UI for debugging
            
        def __del__(self):
            if self.__timer:
                self.__timer.cancel()
                
        def __load_skins(self, skins_path, skinsArray):
            # Initialize the empty skins array
            self.SKINS=[]
            
            # Load each skin
            for skin_name in skinsArray:
                skin={ 'skinName': skin_name }
                skin['startSounds']=        self.__init_sounds(skins_path + skin_name + "\\sounds\\start\\")
                self.__update_progress_bar()
                skin['chingSounds']=        self.__init_sounds(skins_path + skin_name + "\\sounds\\defense\\")
                self.__update_progress_bar()
                skin['hitSounds']=          self.__init_sounds(skins_path + skin_name + "\\sounds\\hit\\")
                self.__update_progress_bar()
                skin['whooshSounds']=       self.__init_sounds(skins_path + skin_name + "\\sounds\\attack\\")
                self.__update_progress_bar()
                skin['deathSounds']=        self.__init_sounds(skins_path + skin_name + "\\sounds\\death\\")
                self.__update_progress_bar()
                skin['humSounds']=          self.__init_sounds(skins_path + skin_name + "\\sounds\\hum\\")
                self.__update_progress_bar()
                skin['backgroundImage']=    self.__load_image(skins_path + skin_name + '\\images\\fight_bg.png')
                self.__update_progress_bar()
                skin['hitImage']=           self.__load_image(skins_path + skin_name + '\\images\\hit_1.png')
                self.__update_progress_bar()
                skin['defendImage']=        self.__load_image(skins_path + skin_name + '\\images\\defend_1.png')
                self.__update_progress_bar()
                skin['healthImages']=[      self.__load_image(skins_path + skin_name + '\\images\\health_1.png'),
                                            self.__load_image(skins_path + skin_name + '\\images\\health_2.png'),
                                            self.__load_image(skins_path + skin_name + '\\images\\health_3.png')]
                self.__update_progress_bar()
                skin['deadImage']=          self.__load_image(skins_path + skin_name + '\\images\\dead.png')
                self.__update_progress_bar()
                skin['wonImage']=           self.__load_image(skins_path + skin_name + '\\images\\won.png')
                self.__update_progress_bar()
                skin['challengeImage']=     self.__load_image(skins_path + skin_name + '\\images\\waiting_for_challenge.png')
                self.__update_progress_bar()                
                skin['hitImageMask']=       self.__load_mask_for(skins_path + skin_name + '\\images\\hit_1_mask.png', skin['hitImage'])
                self.__update_progress_bar()
                skin['defendImageMask']=    self.__load_mask_for(skins_path + skin_name + '\\images\\defend_1_mask.png', skin['defendImage'])
                self.__update_progress_bar()
                skin['healthImageMasks']=  [self.__load_mask_for(skins_path + skin_name + '\\images\\health_1_mask.png', skin['healthImages'][0]),
                                            self.__load_mask_for(skins_path + skin_name + '\\images\\health_2_mask.png', skin['healthImages'][1]),
                                            self.__load_mask_for(skins_path + skin_name + '\\images\\health_3_mask.png', skin['healthImages'][2])]
                self.__update_progress_bar()
                skin['deadImageMask']=      self.__load_mask_for(skins_path + skin_name + '\\images\\dead_mask.png', skin['deadImage'])
                self.__update_progress_bar()
                skin['wonImageMask']=       self.__load_mask_for(skins_path + skin_name + '\\images\\won_mask.png', skin['wonImage'])
                self.__update_progress_bar()
                skin['challengeMask']=       self.__load_mask_for(skins_path + skin_name + '\\images\\waiting_for_challenge_mask.png', skin['challengeImage'])
                self.__update_progress_bar()
                self.SKINS.append(skin)
            
        def initialize(self):
            
            if self.debug_ui:
                debug_skins=['sword','lightsaber']
                self.__progress_per_skin_section=1.0/(len(debug_skins)*19)
                self.__load_skins(self.__SKINS_PATH, debug_skins)
                return
            
            # Check to see if skins directory exists
            if not os.path.exists(self.__SKINS_PATH):
                log("No skin directory found\n\nYou must download at least one skin to this phone")
                return False

            # Create the canvas
            appuifw.app.orientation='portrait'
            appuifw.app.screen='large'
            self.__canvas=appuifw.Canvas ( redraw_callback=self.__handle_redraw, event_callback=self.__handle_event )
            appuifw.app.body=self.__canvas

            # Create an offscreen buffer - draw onto this in the __handle_redraw method and then blit onto the main canvas
            self.__buffer=graphics.Image.new(self.__canvas.size)            

            # Show the loading image
            self.__loading_image=self.__load_image(self.__DATA_PATH+"loading_image.png")
            self.__buffer.blit(self.__loading_image)
            self.__canvas.blit(self.__buffer)
            
            # Check the skins directory and get the subdirs
            skinsArray = os.listdir(self.__SKINS_PATH)
            numSkins=len(skinsArray)
            
            # We need at least one directory in the skins path, so check and proceed if there is one
            if 0==numSkins:
                log("No skins found.  You might need to reinstall, or alternatively put some skins in the e:\data\phonefight\skins directory")
                return False
                
            # Initialize some vars for the loading bar
            self.__progress_per_skin_section=1.0/(19 * numSkins) # There are 17 different sections for skins

            self.__load_skins(self.__SKINS_PATH, skinsArray)
                
            # Initialize the ui to be the first skin in the SKINS array
            self.__skin=self.SKINS[0]
            log( "Initial skin set to : " + self.__skin["skinName"] )
            
            # Make sure that the background gets drawn immediately
            self.__handle_redraw(None)

            # Start the refresh timer
            self.__timer=e32.Ao_timer()
            self.__timer.after(UI.__FRAME_INTERVAL, self.__update_ui)
            
            # If we get here, we have initialized properly
            self.__initialized=True
            self.__start_hum();
            return True
            
        def __update_progress_bar(self):
            self.__loading_progress+=self.__progress_per_skin_section
            
            if self.__buffer != None and self.__canvas!=None:
                self.__buffer.blit(self.__loading_image)
                size=self.__loading_progress * 209.0
                self.__buffer.rectangle((16,126, 16+size,141), fill=(255,0,128) )
                self.__canvas.blit(self.__buffer)
            else:
                log("Progress : %f" % self.__loading_progress)

        # Loads the specified image or returns a 1x1 blank image in case of an error
        def __load_image(self, src):
            try:
                img=graphics.Image.open(src)
                return img
            except:
                img=graphics.Image.new((1,1))
                log("Image "+src+" failed to load")
                return img

        def __init_sound(self, path):
            try:
                s = audio.Sound.open(path)
                s.set_volume(self.__volume)
                return s
            except:
                log( "Warning - sound sample "+path+" not found")
                return None

        def __init_sounds(self, path):
            sounds = []
            try:
               listing = os.listdir(path)
               return map(lambda f: self.__init_sound((path + f)), listing )
            except:
               log( "Warning - error loading sounds from "+path )
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
                log ("Image "+mask_src+" not loaded (as mask)")
                return img

        def __update_ui(self):
            self.__handle_redraw(None)
            self.__timer.after(UI.__FRAME_INTERVAL, self.__update_ui)

        def __handle_event(self, event):
            #self.__handle_redraw(None)
            pass

        def __handle_redraw(self, rect=None):
            if self.__canvas!=None and self.__buffer!=None:
                try:
                    # Put the background image in place
                    self.__buffer.blit(self.__skin['backgroundImage'])
                except:
                    pass
                
                try:
                    if True==self.__waiting:
                        self.__buffer.blit(self.__skin['challengeImage'], mask=self.__skin['challengeMask'])
                    else:
                        # Add your health, if we know it yet
                        if False == self.__practicing:
                            if self.__max_health>0:
                                if self.__playing:
                                    healthImageNumber=int(math.ceil((float(self.__health)/self.__max_health) * (len(self.__skin['healthImages']))-1))
                                    self.__buffer.blit(self.__skin['healthImages'][healthImageNumber], mask=self.__skin['healthImageMasks'][healthImageNumber])
                                else:
                                    if self.__won:
                                        self.__buffer.blit(self.__skin['wonImage'], mask=self.__skin['wonImageMask'])
                                    else:
                                        self.__buffer.blit(self.__skin['deadImage'], mask=self.__skin['deadImageMask'])
                except:
                    pass
                
                try:
                    if self.__popup_counter>0:
                        # Render the popup image
                        try:
                            if self.__popup_mask:
                                self.__buffer.blit(self.__popup_image, mask=self.__popup_mask)
                            else:
                                self.__buffer.blit(self.__popup_image)
                        except:
                            pass                                
                            
                        # Decrement the popup counter
                        self.__popup_counter-=self.__FRAME_INTERVAL
                    else:
                        self.__popup_counter=0
                except:
                    pass

                # We always have _something_ to show on the canvas, even if the previous stuff failed at some point
                self.__canvas.blit(self.__buffer)

        def __hum_callback(self, prev_state, current_state, error):
            if self.__initialized:
                if prev_state == audio.EPlaying and current_state==audio.EOpen:
                    self.__stop_hum()
                    self.__start_hum()
                
        def __stop_hum(self):
            # TODO: make sure that NONE of the humsounds are playing... currently we assume that there's only one
            # .wav file in the /hum/ directory.
            if self.__initialized:
                try:
                    self.__skin['humSounds'][0].stop()
                except:
                    pass
    
        def __start_hum(self):
            if self.__initialized:
                try:
                    self.__skin['humSounds'][0].play(times = 600)
                except:
                    pass
                
        def __play_random_sound(self, sound_type, hum=False):
            if self.__initialized:
                try:
                    self.__play_sound(one_of(self.__skin[sound_type]), hum)
                except:
                    pass

        def __play_sound(self, sound, hum=False):
            if self.__initialized:
                if not self.__silent:
                    try:
                        sound.stop()
                        if hum:
                            sound.play(times=1, callback = self.__hum_callback)
                        else:
                            sound.play(times=1)
                    except:
                        pass
                
        def __create_popup(self, image, mask=None):
            self.__popup_counter=2
            self.__popup_image=image
            self.__popup_mask=mask
        
        def __clear_popup(self):
            self.__popup_counter=0;

        def start_anew(self, max_health):
            if self.__initialized:
                self.__max_health=max_health
                self.__health=max_health
                self.__playing=True
                self.__play_random_sound('startSounds', True)
                
        def setPracticing(self, practicing):
            self.__practicing=practicing
            
        def setWaiting(self, waiting):
            self.__waiting=waiting

        def trigger_hit(self, new_health):
            if self.__initialized:
                self.__create_popup(self.__skin['hitImage'], self.__skin['hitImageMask'])
                self.__health=new_health
                self.__play_random_sound('hitSounds', True)
            
        def trigger_defence(self):
            if self.__initialized:
                self.__create_popup(self.__skin['defendImage'], self.__skin['defendImageMask'])
                self.__play_random_sound('chingSounds', True)
        
        def trigger_attack_start(self):
            if self.__initialized:
                self.__play_random_sound('whooshSounds', True)
        
        def trigger_dead(self):
            if self.__initialized:
                self.__play_random_sound('deathSounds', True)

        def won_or_dead(self, have_we_won):
            self.__playing=False
            self.__won=have_we_won
            
        def set_skin(self, new_skin):
            if self.__initialized:
                self.__stop_hum()
                log(" Changing skin: " + new_skin["skinName"])
                self.__skin=new_skin
                self.__clear_popup()
                self.__play_random_sound('startSounds', True)     
            
        def setSilent(self, silent):
            if self.__initialized:
                self.__silent=silent
                if silent:
                    self.__stop_hum()
                else:
                    self.__start_hum()


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
            self.orientation_history = zeros(HISTORY_SIZE)
            self.index = 0
            self.game_over = False
            self.quitting = False

            appuifw.app.exit_key_handler = self.quit
            appuifw.app.menu = [ (u"Choose skin", tuple([(unicode(skin["skinName"].title()), self.skin_changer(skin)) for skin in ui.SKINS]) ),
                                 (u"Sound on", self.sound_on),
                                 (u"Sound off", self.sound_off),
                                 (u"Back to the fight", self.back_to_fight),
                                 (u"Back to main menu", self.quit) ]

            self.__timer = e32.Ao_timer()

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
            
        def back_to_fight(self):
            pass
            
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

            self.__timer.cancel()
            axyz.disconnect()
            self.rotation_sensor.disconnect()

            ui.won_or_dead(self.won)

            return (self.won, self.quitting)

        def quit(self):
            self.game_over = True
            self.quitting = True
            self.eventlock.signal()

        def new_rotation_data(self, orientation):
            log("orientation: %s" % ORIENTATION_AS_STRING[orientation])
            self.orientation = orientation

        def new_accel_data(self, x, y, z):
            magnitude = math.sqrt(x ** 2 + y ** 2 + z ** 2)
            self.orientation_history[self.index] = self.orientation
            self.index = (self.index + 1) % HISTORY_SIZE

            now = self.elapsed_time
            if now > (self.last_attack + QUIET_INTERVAL) and magnitude > ATTACK_THRESHOLD:
                # index is now pointing to an event in the recent past
                orientation_then = self.orientation_history[self.index]

                if (orientation_then == sensor.orientation.LEFT
                    or orientation_then == sensor.orientation.RIGHT):
                    log("outgoing horizontal attack")
                    self.event = OUTGOING_HORIZONTAL_ATTACK_EVENT
                else:
                    log("outgoing vertical attack")
                    self.event = OUTGOING_VERTICAL_ATTACK_EVENT

                self.last_attack = now

                self.eventlock.signal()

        def defend(self, event):
            # should check for stability?
            if (event == INCOMING_VERTICAL_ATTACK_EVENT):
                log("incoming vertical attack!")
                succeeded = (self.orientation == sensor.orientation.LEFT
                             or self.orientation == sensor.orientation.RIGHT)
            else:
                log("incoming horizontal attack!")
                succeeded = (self.orientation == sensor.orientation.TOP)

            if succeeded:
                log("defence succeeded!")
                ui.trigger_defence()
            else:
                self.health -= 1
                if self.health:
                    log("you're hit, health now %d!" % self.health )
                    ui.trigger_hit(self.health)
                else:
                    self.dead()

        def dead(self):
            log("you lose!")
            self.sock.send(VICTORY_MESSAGE)
            self.game_over = True
            ui.trigger_dead()

        def victory(self):
            log("you win!")
            self.game_over = True
            self.won = True

        def attack(self, event):
            ui.trigger_attack_start()
            if self.sock:
                if event == OUTGOING_HORIZONTAL_ATTACK_EVENT:
                    message = HORIZONTAL_ATTACK_MESSAGE
                else:
                    message = VERTICAL_ATTACK_MESSAGE

                log("sending: %s" % message )
                self.sock.send(message)

        def tick(self):
            self.elapsed_time += TICK_INTERVAL
            self.__timer.after(TICK_INTERVAL, self.tick)

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
        log("Attempting to create server")
        try:
            server = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
            server.bind(("", BT_CHANNEL))
            server.listen(1)
            socket.set_security(server, socket.AUTH | socket.AUTHOR)
            socket.bt_advertise_service(BT_SERVICE_NAME, server, True, socket.RFCOMM)
            conn, client_addr = server.accept()
            return conn
        except:
            log("Failed to create connection")
            return None
    
    def client_socket():
        log("Attempting to discover servers")
        # Get the device from a menu
        device=lightblue.selectdevice()
        
        # Was a device chosen
        if device:
            try:
                # Connect to the device
                conn = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
                conn.connect((device[0], BT_CHANNEL))
                return conn
            except:
                log("Failed to connect to %s"%device[1])
        
        # We get here, we didn't connect
        return None
  
    def quit_app():
        appuifw.app.set_exit()
        

    def practice_mode():
        log("PRACTICE MODE")
        ui.setPracticing(True)
        fight = Fight(PRACTICE_MODE, None)
        fight.play()
        
    def fight(play_mode, sock):
        sock.setblocking(0)
        playing = True
        ui.setPracticing(False)

        while playing:
            log("FIGHT!")
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
        
        
        
    # Initialize the UI
    play_mode=None
    ui=UI()
    result=ui.initialize()
    if False==result:
        log("The UI failed to initialize")
        appuifw.app.set_exit()
    
    quit=False

    # Start a fight.
    while not quit:
        # Options in the main menu
        CHAMPION_MODE, CHALLENGER_MODE, PRACTICE_MODE, CHANGE_SKIN, TIME_TO_QUIT = 0, 1, 2, 3, 4
        menu_choice = appuifw.popup_menu([u"I am the champion",
                                        u"I am the challenger",
                                        u"I need practice",
                                        u"Change skin",
                                        u"Quit"],
                                       u"Select mode of play")
        
        if menu_choice == TIME_TO_QUIT:
            quit = True
        elif menu_choice == CHANGE_SKIN:
            skin_id=appuifw.popup_menu([(unicode(skin["skinName"].title())) for skin in ui.SKINS])
            ui.set_skin(ui.SKINS[skin_id])
        elif menu_choice == PRACTICE_MODE:
            practice_mode()
        else:
            sock = None
            ui.setWaiting(True)
            
            try:
                if menu_choice == CHAMPION_MODE:
                    log("Entering Champion Mode")
                    sock = server_socket()
                elif menu_choice == CHALLENGER_MODE:
                    log("Entering Challenger Mode")
                    sock = client_socket()
            except:
                log("There's been an error in bluetooth selection")
                
            ui.setWaiting(False)
    
            if sock:
                fight(menu_choice, sock)
            else:
                log("No valid bluetooth socket selected")

    quit_app()
    
    


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
