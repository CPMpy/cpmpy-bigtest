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
    #list of mutators and the amount of constraints they accept.
    mm_mutators = [(xor_morph,2),(and_morph,2),(or_morph,2),(implies_morph,2),(not_morph,1),
                   (negated_normal_morph,1),(linearize_constraint_morph,0), (flatten_morph,0), (only_numexpr_equality_morph,0), (normalized_numexpr_morph,1), (normalized_boolexpr_morph,1)]
    enb = 0 #error counter to name files

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
            m, arity = random.choice(mm_mutators)
            # an error can occur in the transformations, so even before the solve call.
            # log function and arguments in that case
            try:
                if arity == 0: #random number of constraints
                    randcons = random.choices(cons,k=len(cons))
                else:
                    randcons = random.choices(cons,k=arity)
                cons += m(randcons)  # apply a metamorphic mutation
            except Exception as args:
                enb += 1
                with open("internalfunctioncrash"+str(enb), "wb") as f:
                    pickle.dump([m, randcons], file=f) #log function and arguments that caused exception
                print('IE', end='', flush=True)
                return True # no need to solve model we didn't modify..


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
        with open("lasterrormodel" + str(enb), "wb") as f:
            pickle.dump(model, file=f)
        print(model)
        return False


'''TRUTH TABLE BASED MORPHS'''
def not_morph(con):
    ncon = ~random.choice(con)
    return [~ncon]
def xor_morph(cons):
    '''morph two constraints with XOR'''
    con1, con2 = cons
    #add a random option as per xor truth table
    return [random.choice((
        Xor([con1, ~con2]),
        Xor([~con1, con2]),
        ~Xor([~con1, ~con2]),
        ~Xor([con1, con2])))]

def and_morph(cons):
    '''morph two constraints with AND'''
    con1, con2 = cons
    return [random.choice((
        ~((con1) & (~con2)),
        ~((~con1) & (~con2)),
        ~((~con1) & (con2)),
        ((con1) & (con2))))]

def or_morph(cons):
    '''morph two constraints with OR'''
    con1, con2 = cons
    #add all options as per xor truth table
    return [random.choice((
        ((con1) | (~con2)),
        ~((~con1) | (~con2)),
        ((~con1) | (con2)),
        ((con1) | (con2))))]

def implies_morph(cons):
    '''morph two constraints with ->'''
    con1, con2 = cons
    #add all options as per xor truth table
    return [random.choice((
        ~((con1).implies(~con2)),
        ((~con1).implies(~con2)),
        ((~con1).implies(con2)),
        ((con1).implies(con2))))]

'''CPMPY-TRANSFORMATION MORPHS'''


def flatten_morph(randcons):
        flatcons = flatten_constraint(randcons)
        return flatcons


def only_numexpr_equality_morph(randcons,supported=frozenset()):
    newcons = only_numexpr_equality(randcons, supported=supported)
    return newcons


def normalized_boolexpr_morph(randcon):
    con, newcons = normalized_boolexpr(randcon)
    return newcons.append(con)

def normalized_numexpr_morph(randcon):
    #TODO should call this on subexpressions, so it's actually called on numexpressions as well
    con, newcons = normalized_numexpr(randcon)
    return newcons.append(con)

def negated_normal_morph(con):
    return [~negated_normal(con)]

def linearize_constraint_morph(cons):
    #only apply linearize after flattening
    flatcons = flatten_constraint(cons)
    lincons = linearize_constraint(flatcons)
    return lincons


if __name__ == '__main__':
    dirname = "models"
    solver = "ortools"
    iters = 5 # number of metamorphic mutations per model
    sat = True
    while sat:
        pass
        sat = metamorphic_test(dirname, solver, iters)
