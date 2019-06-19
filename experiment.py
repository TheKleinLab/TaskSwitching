__author__ = "Austin Hurst"


# Import required KLibs classes and functions

import klibs
from klibs.KLConstants import STROKE_INNER, RC_KEYPRESS, TK_MS
from klibs import P
from klibs import KLUtilities as util
from klibs.KLUserInterface import any_key, ui_request
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import fill, flip, blit, clear
from klibs.KLCommunication import message
from klibs.KLKeyMap import KeyMap
from klibs.KLTime import CountDown
from klibs.KLEventInterface import TrialEventTicket as ET

# Import other required packages

import sdl2
from sdl2.sdlmixer import Mix_QuickLoad_RAW, Mix_PlayChannel, Mix_Playing, Mix_VolumeChunk
import random
import numpy as _np
import ctypes
import time
from copy import copy

# Define colours to be used

BLACK = [0,0,0]
WHITE = [255,255,255]
GREEN = [0,255,0]
RED   = [255,0,0]


class TaskSwitching(klibs.Experiment):

    def setup(self):
        
        # NOTE: 'Cue' refers to the red or green border around the edges of the screen, keeping
        # terminology consistent with Hunt & Klein (2002) on which the stimuli are based. 
        # Since it is always drawn on the screen (i.e. has no onset), it is not really a cue
        # in the usual sense of the word.
        
        # Stimulus Sizes
        
        shape_width   = util.deg_to_px(1.0, even=True) # for circle & markers
        circle_stroke = util.deg_to_px(0.4, even=True)
        square_stroke = util.deg_to_px(0.1, even=True) # for markers & cues
        cue_offset = util.deg_to_px(5.0, even=True) # 1.05 in original, adapted for large modern displays
        cue_height = P.screen_y - cue_offset
        cue_width  = P.screen_x - cue_offset
        
        # Stimulus Colours
        
        marker_stroke      = [square_stroke, WHITE, STROKE_INNER]
        self.compatible    = [square_stroke, GREEN, STROKE_INNER]
        self.incompatible  = [square_stroke, RED, STROKE_INNER]
        
        # Stimulus Drawbjects
        
        self.middle_circle = kld.Annulus(shape_width, circle_stroke, fill=WHITE).render()
        self.middle_x = kld.FixationCross(shape_width, square_stroke, fill=WHITE, rotation=45).render()
        
        self.cue_prerender = kld.Rectangle(cue_width, height=cue_height) # stroke is set during prep
        
        self.empty_marker  = kld.Rectangle(shape_width, stroke=marker_stroke).render()
        self.filled_marker = kld.Rectangle(shape_width, stroke=marker_stroke, fill=WHITE).render()
        
        # Layout
        
        flanker_offset      = util.deg_to_px(8, even=True)
        self.flanker_pos_l  = (P.screen_c[0] - flanker_offset, P.screen_c[1])
        self.flanker_pos_r  = (P.screen_c[0] + flanker_offset, P.screen_c[1])
        
        # Response Mapping
        
        self.keymap = KeyMap(
            "responses", # Name
            ['z', '/'], # UI labels
            ['L', 'R'], # Data labels
            [sdl2.SDLK_z, sdl2.SDLK_SLASH] # SDL2 Keysyms
        )
        
        # Event Sequence
        
        self.green_first = random.choice([True, False]) # If True, green cue is first.
        

    def block(self):
        
        # Reset SOA list for each block of trials and clear the screen
        
        self.soa_list = copy(P.signal_target_soas) # interval between warning signal and target onset in msec
        clear()
        
        # If first block, display start message and wait for keypress before beginning experiment
        
        if P.block_number == 1:
            fill()
            message("When ready, press any key to begin the experiment.", location=P.screen_c, registration=5)
            flip()
            any_key()
        elif P.block_number == _np.ceil(P.blocks_per_experiment/2.0):
            halfway_msg = ("Whew! You're halfway done.\n"
                "Take a break if you need, and press any key to continue.")
            fill()
            message(halfway_msg, location=P.screen_c, registration=5, align='center')
            flip()
            any_key()
        

    def setup_response_collector(self):
        
        # Configure ResponseCollector to get 'z' and '/' keypresses as responses
        
        self.rc.uses([RC_KEYPRESS])
        self.rc.terminate_after = [1000, TK_MS] # 1000ms timeout for responses
        self.rc.flip = False
        self.rc.keypress_listener.key_map = self.keymap
        self.rc.keypress_listener.interrupts = True


    def trial_prep(self):
        
        # Define variables for trial
        
        # Choose random target onset from range defined in params (2000-6000ms default)
        
        self.target_onset = self.random_interval(P.target_onset_range[0], P.target_onset_range[1])
        
        # Alternate SOA condition every run of 16 trials (8 compatible, 8 incompatible)
        
        if P.trial_number % 16 == 1:
            self.soa = random.choice(self.soa_list)
            self.soa_list.remove(self.soa)
        
        # Set stroke of cue to green or red, alternating every 8 trials
        
        if self.green_first:
            self.cuetype = "compatible" if int((P.trial_number-1)/8) % 2 == 0 else "incompatible"
        else:
            self.cuetype = "compatible" if int((P.trial_number-1)/8) % 2 == 1 else "incompatible"
        
        if self.cuetype == "incompatible":
            self.cue_prerender.stroke = self.incompatible # Red cue
            self.cue = self.cue_prerender.render()
        elif self.cuetype == "compatible":
            self.cue_prerender.stroke = self.compatible # Green cue
            self.cue = self.cue_prerender.render()
        
        # Add timecourse of events to EventManager
        
        signal_duration = 100 if self.soa != 0 else 0 # no signal on 0 soa trials
        events = [[self.target_onset - self.soa, 'signal_on']]
        events.append([events[-1][0] + signal_duration, 'signal_off'])
        events.append([self.target_onset, 'target_on'])
        for e in events:
            self.evm.register_ticket(ET(e[1], e[0]))
            
        # Generate background and signal noises for trial
        
        self.background_noise = self.generate_noise(12, dichotic=False, volume=64)
        if P.signal_type == "exo":
            self.signal_noise = self.generate_noise(1, dichotic=False, volume=128)
        else:
            self.signal_noise = self.generate_noise(1, dichotic=True, volume=64)
            
        # Start playing background noise
        
        Mix_PlayChannel(1, self.background_noise, -1)
        

    def trial(self):
        
        if P.development_mode:
            print(self.soa, self.target_onset, self.target_loc, self.cuetype)
        
        # Present stiumuli in seqence with timing as defined in trial_prep
        
        signal_on = False
        self.display_refresh(target=None)
        
        while self.evm.before('target_on'):
            
            ui_request()
            if self.evm.between('signal_on', 'signal_off') and not signal_on:
                Mix_PlayChannel(1, self.signal_noise, -1) # switch to playing signal
                signal_on = True
            elif self.evm.after('signal_off') and signal_on:
                Mix_PlayChannel(1, self.background_noise, -1) # turn signal off
                signal_on = False
        
        Mix_PlayChannel(1, self.background_noise, -1) # make sure signal's off, just in case

        # Display target and wait for keyboard response (or 1000ms timeout interval)
        
        self.display_refresh(target=self.target_loc)
        self.rc.collect()

        # Prepare trial data for entering into database
        
        response = self.rc.keypress_listener.response(rt=False) # get key pressed
        if response != "NO_RESPONSE":
            if self.cuetype == "incompatible":
                self.accuracy = int(response != self.target_loc)
            elif self.cuetype == "compatible":
                self.accuracy = int(response == self.target_loc)
            self.rt = self.rc.keypress_listener.response(value=False) # get reaction time
        else:
            response      = "timeout"
            self.accuracy = "NA"
            self.rt       = "NA"
            
        # Display feedback for 1000ms following response. If response was accurate, display RT 
        # in place of fixation. If inaccurate, display red fixation to indicate error.
        
        feedback_period = CountDown(1)
        self.display_refresh(target=None, feedback=True)
        while feedback_period.counting():
            ui_request()
            
        if P.development_mode:
            print(response, self.accuracy, self.rt)
            print("")

        return {
            "block_num":   P.block_number,
            "trial_num":   P.trial_number,
            "signal_type": P.signal_type,
            "cue_type":    self.cuetype,
            "soa":         self.soa if self.soa != 0 else "None",
            "target_loc":  self.target_loc,
            "response":    response,
            "accuracy":    self.accuracy,
            "rt":          self.rt
        }


    def trial_clean_up(self):
        pass


    def clean_up(self):
        pass
        
        
    def display_refresh(self, cue=True, target=None, feedback=False):
        
        # Draw screen elements that are always present during a trial
        
        fill(BLACK)
        blit(self.empty_marker,  5, self.flanker_pos_l)
        blit(self.empty_marker,  5, self.flanker_pos_r)
        
        # Draw additional elements if present
        
        if cue:
            blit(self.cue, 5, P.screen_c)
        
        if feedback:
            if self.accuracy == 1: # If correct response, display RT in place of fixation
                message("{0}".format(int(self.rt)), location=P.screen_c, registration=5)
            elif self.accuracy == 0: # If incorrect response, display fixation as red
                blit(self.middle_x, 5, P.screen_c)
            elif self.accuracy == "NA": # If no response, display timeout feedback
                message("Too slow!", location=P.screen_c, registration=5)
                
        else:
            blit(self.middle_circle, 5, P.screen_c)
        
        if target == "L":
            blit(self.filled_marker, 5, self.flanker_pos_l)
        elif target == "R":
            blit(self.filled_marker, 5, self.flanker_pos_r)
            
        flip()


    ## Utility Functions ##
        
    def random_interval(self, lower, upper, refresh=60): 
        
        # utility function to generate random interval respecting the refresh rate of the monitor,
        # since stimuli can only be changed at refreshes. Converts upper/lower bounds in ms to
        # flips per the refresh rate, selects random number of flips, then converts flips back to ms.
        
        time_per_flip = 1000.0/refresh
        min_flips = int(round(lower/time_per_flip))
        max_flips = int(round(upper/time_per_flip))
        
        return random.choice(range(min_flips, max_flips, 1)) * time_per_flip
        
        
    def generate_noise(self, duration, sample_rate=22050, multiplier=1, dichotic=False, volume=64):
        # Code borrowed from Mike Lawrence, I don't fully understand how it works yet.
        max_int = 2**16/4 # 16384, what is this?
        dtype = _np.int16
        size = int(duration*sample_rate)
    
        if dichotic:
            noise_L = _np.random.randint(-max_int*multiplier, max_int*multiplier, size, dtype)
            noise_R = _np.random.randint(-max_int*multiplier, max_int*multiplier, size, dtype)
            noise_arr = _np.c_[noise_L,noise_R]
        else:
            noise   = _np.random.randint(-max_int*multiplier, max_int*multiplier, size).astype('int16')
            noise_arr = _np.c_[noise,noise]

        # Take randomly generated noise and convert that to an SDL Mix_Chunk
        noise_arr.dtype = dtype
        wav_string = noise_arr.tostring()
        buflen = len(wav_string)
        buf = (ctypes.c_ubyte * buflen).from_buffer_copy(wav_string)
        noise_SDLsample = Mix_QuickLoad_RAW(ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)), ctypes.c_uint(buflen))
        Mix_VolumeChunk(noise_SDLsample, volume)
        
        return noise_SDLsample
