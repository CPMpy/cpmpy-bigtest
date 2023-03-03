import brotli
import glob
import os
import pickle
import time
from os.path import join
import argparse
import random

from cpmpy.transformations.linearize import linearize_constraint

from cpmpy import *
from cpmpy.expressions.utils import is_any_list
from cpmpy.transformations.flatten_model import flatten_constraint, normalized_boolexpr, normalized_numexpr, \
    negated_normal
from cpmpy.transformations.reification import only_bv_implies, reify_rewrite
from cpmpy.transformations.comparison import only_numexpr_equality


def lists_to_conjunction(cons):
    # recursive...
    return [any(lists_to_conjunction(c)) if is_any_list(c) else c for c in cons]


def metamorphic_test(dirname, solver, iters):
    mm_mutators = [xor_morph,and_morph,or_morph,implies_morph,not_morph]
    mm_mutators = [negated_normal_morph]
    mm_mutators = [linearize_constraint_morph]

    # choose a random model
    fmodels = glob.glob(join(dirname, "*.bt"))
    f = random.choice(fmodels)
    #f = "models\\cp_explanations16650512278054872.bt" has no constraints
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
            sat = model.solve(solver=solver, time_limit=20)
            if model.status().runtime > 15:
                # timeout, skip
                print('s', end='', flush=True)
                return True
            elif sat:
                # has to be SAT...
                print('.', end='', flush=True)
                return True
            else:
                print('X', end='', flush=True)
                print('lastmorph: ', m)
        except Exception as e:
            print('E', end='', flush=True)
            print(e)

        # if you got here, the model failed...
        with open("lasterrormodel", "wb") as f:
            pickle.dump(model, file=f)
        print(model)


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

'''TRUTH TABLE BASED MORPHS'''
def not_morph(cons):
    con = ~random.choice(cons)
    cons.append(~con)
    return cons
def xor_morph(cons):
    '''morph two constraints with XOR'''
    # choose constraints
    con1, con2 = random.choices(cons, k=2)
    #add a random option as per xor truth table
    cons.append(random.choice((
        Xor([con1, ~con2]),
        Xor([~con1, con2]),
        ~Xor([~con1, ~con2]),
        ~Xor([con1, con2]))))
    return cons

def and_morph(cons):
    '''morph two constraints with AND'''
    # choose constraints
    con1, con2 = random.choices(cons, k=2)
    cons.append(random.choice((
        ~((con1) & (~con2)),
        ~((~con1) & (~con2)),
        ~((~con1) & (con2)),
        ((con1) & (con2)))))
    return cons

def or_morph(cons):
    '''morph two constraints with OR'''
    # choose constraints
    con1, con2 = random.choices(cons, k=2)
    #add all options as per xor truth table
    cons.append(random.choice((
        ((con1) | (~con2)),
        ~((~con1) | (~con2)),
        ((~con1) | (con2)),
        ((con1) | (con2)))))
    return cons

def implies_morph(cons):
    '''morph two constraints with ->'''
    # choose constraints
    con1, con2 = random.choices(cons, k=2)
    #add all options as per xor truth table
    cons.append(random.choice((
        ~((con1).implies(~con2)),
        ((~con1).implies(~con2)),
        ((~con1).implies(con2)),
        ((con1).implies(con2)))))
    return cons

'''CPMPY-TRANSFORMATION MORPHS'''

def flatten_morph(cons):
    randcons = random.choices(cons, k=len(cons))

    try:
        flatcons = flatten_constraint(randcons)
        return cons + flatcons
    except Exception:
        print("flatten_constraint crashed with input:", randcons)
        return cons

def only_numexpr_equality_morph(cons,supported=frozenset()):
    randcons = random.choices(cons, k=len(cons))
    newcons = only_numexpr_equality(randcons, supported=supported)
    return cons + newcons


def normalized_boolexpr_morph(cons):
    randcon = random.choice(cons)
    lastSelectedConstraints = [randcon]
    con, newcons = normalized_boolexpr(randcon)
    cons.append(con)
    cons.extend(newcons)
    return cons

def normalized_numexpr_morph(cons):
    #TODO should call this on subexpressions, so it's actually called on numexpressions as well
    randcon = random.choice(cons)
    lastSelectedConstraints = [randcon]
    con, newcons = normalized_numexpr(randcon)
    cons.append(con)
    cons.extend(newcons)
    return cons

def negated_normal_morph(cons):
    randcon = random.choice(cons)
    try:
        cons.append(~negated_normal(randcon))
        return cons
    except Exception:
        print("negated_normal crashed with input:", randcon)
        with open("internalfunctioncrash", "wb") as f:
            pickle.dump([negated_normal, randcon], file=f)
        return [BoolVal(False)] #to make sure we know something went wrong

def linearize_constraint_morph(cons):
    randcons = random.choices(cons, k=len(cons))
    #only apply linearize after flattening
    flatcons = flatten_constraint(randcons)
    lincons = linearize_constraint(flatcons)
    return cons + lincons


if __name__ == '__main__':
    dirname = "models"
    solver = "ortools"
    iters = 5 # number of metamorphic mutations per model
    sat = True
    while sat:
        pass
        sat = metamorphic_test(dirname, solver, iters)
