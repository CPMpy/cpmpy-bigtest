import brotli
import glob
import os
import pickle
import time
import traceback  # for exception printing
from os.path import join

import pandas as pd
import cpmpy as cp
from tqdm import tqdm


def run_model_stats(dirname, solvername="ortools"):
    # will make dataframe
    headers = ["fname", "load", "add", "solve", "solver", "sat"]
    data = []  # append row by row
    for fname in tqdm(sorted(glob.glob(join(dirname, "*.bt")))):
        try:
            with open(fname, 'rb') as fpcl:
                t0 = time.time()
                model = pickle.loads(brotli.decompress(fpcl.read()))
                cpm_cons = model.constraints
                load = time.time() - t0

                s = cp.SolverLookup.get(solvername)
                t0 = time.time()
                s += cpm_cons
                add = time.time() - t0

                t0 = time.time()
                sat = s.solve()
                solve = time.time() - t0
                solver = s.status().runtime

                data.append([fname, load, add, solve, solver, sat])
                if not sat:
                    print(f"\tWARNING, {fname} was unsat")
        except Exception as e:
            print(fname, "CRASHES", e)
            traceback.print_exc()

    # make the dataframe
    df = pd.DataFrame(data, columns=headers)
    df.to_csv("run_models.csv", index=False)

    print("")
    print(df[["load", "add", "solve", "solver"]].describe())


if __name__ == '__main__':
    dirname = "models"
    run_model_stats(dirname)
