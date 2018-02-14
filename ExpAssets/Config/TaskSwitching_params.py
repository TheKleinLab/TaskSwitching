### Klibs Parameter overrides ###

#########################################
# Runtime Settings
#########################################
collect_demographics = True
manual_demographics_collection = False
manual_trial_generation = False
run_practice_blocks = True
multi_user = True
view_distance = 57 # in centimeters, 1cm = 1 deg of visual angle at 57cm away

#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (0, 0, 0, 255)
default_color = (255, 255, 255, 255)
default_font_size = 28
default_font_name = 'Frutiger'

#########################################
# EyeLink Settings
#########################################
manual_eyelink_setup = False
manual_eyelink_recording = False

saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15

#########################################
# Experiment Structure
#########################################
multi_session_project = False
trials_per_block = 64
blocks_per_experiment = 2
table_defaults = {}

#########################################
# Development Mode Settings
#########################################
dm_auto_threshold = True
dm_trial_show_mouse = True
dm_ignore_local_overrides = False
dm_show_gaze_dot = True

#########################################
# Data Export Settings
#########################################
primary_table = "trials"
unique_identifier = "userhash"
default_participant_fields = [[unique_identifier, "participant"], "sex", "age", "handedness"]
default_participant_fields_sf = [[unique_identifier, "participant"], "random_seed", "sex", "age", "handedness"]

#########################################
# PROJECT-SPECIFIC VARS
#########################################

# upper and lower bounds for interval between trial start and target onset (in ms), chosen randomly each trial.
target_onset_range = [2000, 6000]

# interval between warning signal and target onset (in ms), changes every run of 16 trials ('0' indicates no 
# warning signal).
signal_target_soas = [0, 50, 200, 800]

# whether to use endogenous or exogenous auditory signals
signal_type = "exo"
