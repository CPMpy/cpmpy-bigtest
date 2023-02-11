import brotli
import glob
import os
import pickle
from os.path import join

from cpmpy import *
from cpmpy.transformations.flatten_model import flatten_constraint

def print_model_stats(dirname):
    for f in sorted(glob.glob(join('..', dirname, "*.bt"))):
        try:
            with open(f, 'rb') as fpcl:
                model = pickle.loads(brotli.decompress(fpcl.read()))
                model.solve(time_limit=120)
                if model.status().runtime > 100:
                    print(f"git mv {f} models/slow/")
                print("\t", f, "\t", len(model.constraints), len(flatten_constraint(model.constraints)), "\t", model.status())
        except Exception as e:
            print(f, "CRASHES", e)


if __name__ == '__main__':
    dirname = "models"
    print_model_stats(dirname)
