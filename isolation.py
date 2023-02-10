import sys
import copy
from cpmpy import *
from cpmpy.solvers.ortools import CPM_ortools
from cpmpy.solvers.gurobi import CPM_gurobi
from cpmpy.transformations.get_variables import get_variables
from cpmpy.transformations.flatten_model import flatten_constraint,flatten_model

def isolation(constraints, solver="gurobi", verbose=False):
    #isolation technique

    m = Model(constraints)
    #m = flatten_model(m)
    m.solve(solver=solver)
    status = m.status().exitstatus.name
    if status != "UNSATISFIABLE":
        return []

    failing = m.constraints
    passing = []
    LatestWasFail = True
    while True:
        if LatestWasFail:
            newPart = failing[:len(failing)-int((len(failing)-len(passing))/2)]
            m = Model(newPart)
        else:
            newPart = failing[:len(passing)+int((len(failing)-len(passing))/2)]
            m = Model(newPart)

        m.solve(solver=solver)
        
        status = m.status().exitstatus.name
        if status == "UNSATISFIABLE":
            failing = m.constraints
            LatestWasFail = True
            if len(failing) - len(passing) <= 1:
                return passing, failing
        else:
            passing = m.constraints
            LatestWasFail = False

    return passing, failing