__author__ = "Austin Hurst"


# Import required KLibs classes and functions

import klibs
from klibs.KLConstants import *
from klibs import P
from klibs import KLUtilities as util
from klibs.KLUserInterface import any_key
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import fill, flip, blit, clear
from klibs.KLCommunication import message
from klibs.KLKeyMap import KeyMap
from klibs.KLEventInterface import TrialEventTicket as ET


# Import other required packages

import sdl2
from sdl2.sdlmixer import (Mix_QuickLoad_WAV, Mix_QuickLoad_RAW, Mix_LoadWAV, Mix_PlayChannel,
    Mix_Playing, Mix_VolumeChunk)
import random
import numpy as _np
import ctypes
import time

# Define colours to be used

BLACK = [0,0,0]
WHITE = [255,255,255]
GREEN = [0,255,0]
RED   = [255,0,0]


class TaskSwitching(klibs.Experiment):

    def __init__(self, *args, **kwargs):
        super(TaskSwitching, self).__init__(*args, **kwargs)

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
        self.error_circle  = kld.Annulus(shape_width, circle_stroke, fill=RED).render()
        
        self.cue_prerender = kld.Rectangle(cue_width, height=cue_height) # stroke is set during prep
        
        self.empty_marker  = kld.Rectangle(shape_width, stroke=marker_stroke).render()
        self.filled_marker = kld.Rectangle(shape_width, stroke=marker_stroke, fill=WHITE).render()
        
        # Layout
        
        flanker_offset      = util.deg_to_px(8, even=True)
        self.flanker_pos_l  = (P.screen_c[0] - flanker_offset, P.screen_c[1])
        self.flanker_pos_r  = (P.screen_c[0] + flanker_offset, P.screen_c[1])
        
        # Response Mapping
        
        keymap_name         = "responses"
        keymap_ui_labels    = ['z','/']
        keymap_data_labels  = ['L','R']
        keymap_sdl2_keysyms = [sdl2.SDLK_z, sdl2.SDLK_SLASH]
        
        self.keymap = KeyMap(keymap_name, keymap_ui_labels, keymap_data_labels, keymap_sdl2_keysyms)
        
        # Event Sequence
        
        self.green_first = bool(random.choice(range(0,2,1))) # If True, green cue is first.
        
        #self.background_noise = self.generate_noise(12, dichotic=False)
        

    def block(self):
        
        # Reset SOA list for each block of trials and clear the screen
        
        self.soa_list = [0, 50, 200, 800] # interval between warning signal and target onset in msec
        clear()
        
        # If first block, display start message and wait for keypress before beginning experiment
        
        if P.block_number == 1:
            fill()
            message("When ready, press any key to begin the experiment.", location=P.screen_c, registration=5)
            flip()
            any_key()
        

    def setup_response_collector(self):
        
        # Configure ResponseCollector to get 'z' and '/' keypresses as responses
        
        self.rc.display_callback = self.wait_for_response
        self.rc.terminate_after = [10, TK_S] # 1000ms timeout for responses, not working currently
        self.rc.uses([RC_KEYPRESS])
        self.rc.keypress_listener.interrupts = True
        self.rc.keypress_listener.key_map = self.keymap
        self.rc.flip = False # Disable flipping on each rc loop, since callback already flips

    def trial_prep(self):
        
        # Define variables for trial
        
        self.first_rc_flip = True # True if first flip of rc display callback had not occurred yet
        
        # Choose random target onset from range defined in params (2000-6000ms default)
        
        self.target_onset = self.random_interval(P.target_onset_range[0], P.target_onset_range[1])
        
        # Alternate SOA condition every run of 16 trials (8 compatible, 8 incompatible)
        
        if P.trial_number % 16 == 1:
            self.soa = random.choice(self.soa_list)
            self.soa_list.remove(self.soa)
        
        # Set stroke of cue to green or red, alternating every 8 trials
        
        if self.green_first:
            self.cuetype = "compatible" if ((P.trial_number-1)/8) % 2 == 0 else "incompatible"
        else:
            self.cuetype = "compatible" if ((P.trial_number-1)/8) % 2 == 1 else "incompatible"
        
        if self.cuetype == "incompatible":
            self.cue_prerender.stroke = self.incompatible # Red cue
            self.cue = self.cue_prerender.render()
        elif self.cuetype == "compatible":
            self.cue_prerender.stroke = self.compatible # Green cue
            self.cue = self.cue_prerender.render()
        
        # Add timecourse of events to EventManager
        
        events = [[self.target_onset - self.soa, 'signal_on']]
        events.append([events[-1][0] + 50, 'signal_off'])
        events.append([self.target_onset, 'target_on'])
        for e in events:
            self.evm.register_ticket(ET(e[1], e[0]))
            
        # Generate noise for trial and set volume to 50%
        
        self.background_noise = self.generate_noise(12, dichotic=False)
        #self.background_noise = Mix_LoadWAV("test.wav")
        Mix_PlayChannel(1, self.background_noise, -1)
        Mix_VolumeChunk(self.background_noise, 64)
        

    def trial(self):
        
        #if P.development_mode:
        print(self.soa, self.target_onset, self.target_loc, self.cuetype)
        
        # Present stiumuli in seqence with timing as defined in trial_prep
        
        self.display_refresh(target=None)
        start = time.time()
        
        while self.evm.before('signal_on', True):
            continue
            
        if self.evm.before('target_on', True) and self.evm.before('signal_off', True):
            # This is never run if the SOA is 0.
            Mix_VolumeChunk(self.background_noise, 128) # double volume of noise
            
        while self.evm.before('target_on', True) and self.evm.before('signal_off', True):
            continue
            
        Mix_VolumeChunk(self.background_noise, 64) # return volume to 50% after 50ms
        
        while self.evm.before('target_on', True):
            continue
        
        # Display target and wait for keyboard response (or 1000ms timeout interval)

        self.rc.collect()
        t = time.time() # get time immediately after a response is made

        # Prepare trial data for entering into database
        
        response = self.rc.keypress_listener.response(True, False) # get key pressed
        if response != "NO_RESPONSE":
            if self.cuetype == "incompatible":
                self.accuracy = int(response != self.target_loc)
            elif self.cuetype == "compatible":
                self.accuracy = int(response == self.target_loc)
            #rc_end = self.rc.keypress_listener.response(False, True)
            self.rt = (t - self.rc_start)*1000 # Time between first flip of target and keypress
        else:
            response      = "timeout"
            self.accuracy = "NA"
            self.rt       = "NA"
            
        # Display feedback for 1000ms following response. If response was accurate, display RT 
        # in place of fixation. If inaccurate, display red fixation to indicate error.
        
        while (time.time() - t) < 1 and self.accuracy != "NA":
            self.display_refresh(target=None, feedback=True)
            
        #if P.development_mode:
        print(response, self.accuracy, self.rt)
        print ""

        return {
            "block_num":  P.block_number,
            "trial_num":  P.trial_number,
            "cue_type":   self.cuetype,
            "soa":        self.soa if self.soa != 0 else "None",
            "target_loc": self.target_loc,
            "response":   response,
            "accuracy":   self.accuracy,
            "rt":         self.rt
        }

    def trial_clean_up(self):
        pass

    def clean_up(self):
        pass
        
    def display_refresh(self, cue=True, target=None, feedback=False):
        
        # Draw screen elements that are always present during a trial
        
        fill(BLACK)
        #blit(self.middle_circle, 5, P.screen_c)
        blit(self.empty_marker,  5, self.flanker_pos_l)
        blit(self.empty_marker,  5, self.flanker_pos_r)
        
        # Draw additional elements if present
        
        if cue:
            blit(self.cue, 5, P.screen_c)
        
        if feedback:
            if self.accuracy == 1: # If correct response, display RT in place of fixation
                message("{0}".format(int(self.rt)), location=P.screen_c, registration=5)
            elif self.accuracy == 0: # If incorrect response, display fixation as red
                blit(self.error_circle, 5, P.screen_c)
        else:
            blit(self.middle_circle, 5, P.screen_c)
        
        if target == "L":
            blit(self.filled_marker, 5, self.flanker_pos_l)
        elif target == "R":
            blit(self.filled_marker, 5, self.flanker_pos_r)
            
        flip()
        
        
    def wait_for_response(self):
        # Display target in target location
        self.display_refresh(target=self.target_loc)
        # If first loop of response collection, the time after the first refresh is the true onset
        # of the response period.
        if self.first_rc_flip:
            self.rc_start = time.time()
            self.first_rc_flip = False
        
    def random_interval(self, lower, upper, refresh=60): 
        
        # utility function to generate random interval respecting the refresh rate of the monitor,
        # since stimuli can only be changed at refreshes. Converts upper/lower bounds in ms to
        # flips per the refresh rate, selects random number of flips, then converts flips back to ms.
        
        time_per_flip = 1000.0/refresh
        min_flips = int(round(lower/time_per_flip))
        max_flips = int(round(upper/time_per_flip))
        
        return random.choice(range(min_flips, max_flips, 1)) * time_per_flip
        
    def generate_noise(self, duration, sample_rate=22050, multiplier=1, dichotic=False):
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

        # Take randomly generated noise and convert it to a WAV, then convert that to SDL Mix_Chunk
        noise_arr.dtype = dtype
        #sound_file = cStringIO.StringIO()
        #wavio.write(sound_file, noise_arr, rate=(sample_rate*2))
        #wav_string = sound_file.getvalue()
        wav_string = noise_arr.tostring()
        buflen = len(wav_string)
        buf = (ctypes.c_ubyte * buflen).from_buffer_copy(wav_string)
        noise_SDLsample = Mix_QuickLoad_RAW(ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)), ctypes.c_uint(buflen))
    
        return noise_SDLsample
