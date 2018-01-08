__author__ = 'Austin Hurst'
from klibs.KLIndependentVariable import IndependentVariableSet, IndependentVariable

# NOTE: At present, only one of the independent variables for this experiment (target location)
# is contained in this file due to present limitations of the IndependentVariable class in klibs.
# Target onset is randomly selected from a range defined in the _params.py file, and the signal-target
# intervals are defined in the block setup section of experiment.py.


# Initialize object containing project's independant variables

TaskSwitching_ind_vars = IndependentVariableSet()


# Define project variables and variable types

TaskSwitching_ind_vars.add_variable("target_loc", str, ["L", "R"])
