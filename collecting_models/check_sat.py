import brotli
import glob
import os
import pickle
from os.path import join

from cpmpy import *
from cpmpy.transformations.flatten_model import flatten_constraint
from cpmpy.solvers.solver_interface import ExitStatus

# keep only one model of the same name with the same nr of constraints after flattening
# others are too likely to be structurally near-identical (e.g. only a constant different)

def print_model_stats(dirname):
    for f in sorted(glob.glob(join('..', dirname, "*.bt"))):
        try:
            with open(f, 'rb') as fpcl:
                model = pickle.loads(brotli.decompress(fpcl.read()))
                if not model.solve(time_limit=2):
                    if model.status().exitstatus == ExitStatus.UNSATISFIABLE:
                        sat = False
                        try:
                            sat = model.solve("minizinc", time_limit=60)
                        except:
                            sat = False
                        if sat:
                            continue
                        try:
                            sat = model.solve("z3", time_limit=60)
                        except:
                            sat = False
                        if sat:
                            continue
                        print(f"git mv {f} models_unsat/")
                    
        except Exception as e:
            print(f, "CRASHES", e)


if __name__ == '__main__':
    dirname = "models"
    print_model_stats(dirname)
