import brotli
import glob
import os
import re
import pickle
from os.path import join

from cpmpy import *
from cpmpy.transformations.flatten_model import flatten_constraint

# keep only one model of the same name with the same nr of constraints after flattening
# others are too likely to be structurally near-identical (e.g. only a constant different)

def print_model_stats(dirname):
    data = set()
    for f in sorted(glob.glob(join('..', dirname, "*.bt"))):
        try:
            with open(f, 'rb') as fpcl:
                model = pickle.loads(brotli.decompress(fpcl.read()))
                loc = re.search(r"\d", f)
                name = f[:loc.start()]
                nr = len(flatten_constraint(model.constraints))
                key = (name, nr)
                if key in data:
                    print(f"git rm {f}")
                else:
                    data.add(key)
                    
        except Exception as e:
            print(f, "CRASHES", e)


if __name__ == '__main__':
    dirname = "models"
    print_model_stats(dirname)
