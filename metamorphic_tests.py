import brotli
import glob
import os
import pickle
import time
from os.path import join
import argparse
import random

from cpmpy import *
from cpmpy.expressions.utils import is_any_list
from cpmpy.transformations.flatten_model import flatten_constraint
from cpmpy.transformations.reification import only_bv_implies, reify_rewrite
from cpmpy.transformations.comparison import only_numexpr_equality


def lists_to_conjunction(cons):
    # recursive...
    return [any(lists_to_conjunction(c)) if is_any_list(c) else c for c in cons]


def metamorphic_test(dirname, solver, iters):
    mm_mutators = [metamorphic_negation]

    # choose a random model
    fmodels = glob.glob(join(dirname, "*.bt"))
    f = random.choice(fmodels)
    with open(f, 'rb') as fpcl:
        cons = pickle.loads(brotli.decompress(fpcl.read())).constraints
        assert (len(cons)>0), f"{f} has no constraints"
        # replace lists by conjunctions
        cons = lists_to_conjunction(cons)
        assert (len(cons)>0), f"{f} has no constraints after l2conj"

        for i in range(iters):
            # choose a metamorphic mutation
            m = random.choice(mm_mutators)
            cons = m(cons)  # apply a metamorphic mutation, can change cons inplace

        # enough mutations, time for solving
        try:
            model = Model(cons)
            sat = model.solve(solver=solver, time_limit=120)
            if model.status().runtime > 110:
                # timeout, skip
                print('s', end='', flush=True)
                return True
            elif sat:
                # has to be SAT...
                print('.', end='', flush=True)
                return True
            else:
                print('X', end='', flush=True)
        except Exception as e:
            print('E', end='', flush=True)
            print(e)

        # if you got here, the model failed...
        print(model)
        # save it etc...

        return False


def metamorphic_negation(cons):
    """Applies double negation (optionally with a flatten inbetween)"""

    # choose a constraint
    i = random.randrange(len(cons))
    # choose whether to flatten inbetween
    do_flat = random.choice((True,False))

    # apply double negation
    con = cons[i]
    negcon = ~con
    if do_flat:
        negnegcon = ~(all(flatten_constraint(negcon)))  # flatten returns list
    else:
        negnegcon = ~negcon

    # add as new constraint
    cons.append(negnegcon)
    return cons



if __name__ == '__main__':
    dirname = "models"
    solver = "ortools"
    iters = 5 # number of metamorphic mutations per model

    sat = True
    while sat:
        sat = metamorphic_test(dirname, solver, iters)
