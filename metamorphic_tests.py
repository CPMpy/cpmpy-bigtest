import brotli
import glob
import os
import pickle
import time
from os.path import join
import argparse
import random

from cpmpy.transformations.get_variables import get_variables

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


def metamorphic_test(dirname, solver, iters,fmodels,enb):
    #list of mutators and the amount of constraints they accept.
    mm_mutators = [(xor_morph),(and_morph),(or_morph),(implies_morph),(not_morph),
                   (negated_normal_morph),(linearize_constraint_morph), (flatten_morph), (only_numexpr_equality_morph), (normalized_numexpr_morph), (normalized_boolexpr_morph)]
    #mm_mutators = [add_solution]
    # choose a random model
    f = random.choice(fmodels)
    originalmodel = f
    with open(f, 'rb') as fpcl:
        cons = pickle.loads(brotli.decompress(fpcl.read())).constraints
        assert (len(cons)>0), f"{f} has no constraints"
        # replace lists by conjunctions
        cons = lists_to_conjunction(cons)
        assert (len(cons)>0), f"{f} has no constraints after l2conj"
        assert (Model(cons).solve()), f"{f} is not sat"
        mutators = []
        for i in range(iters):
            # choose a metamorphic mutation
            m = random.choice(mm_mutators)
            # an error can occur in the transformations, so even before the solve call.
            # log function and arguments in that case
            mutators += [m]
            try:
                cons += m(cons)  # apply a metamorphic mutation
            except Exception as exc:
                enb += 1
                function, argument = exc.args
                filename = "internalfunctioncrash"+str(enb)
                with open(filename, "wb") as ff:
                    pickle.dump([function, argument, originalmodel], file=ff) #log function and arguments that caused exception
                print('IE', end='', flush=True)
                return False # no need to solve model we didn't modify..


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
                print('morphs: ', mutators)
        except Exception as e:
            print('E', end='', flush=True)
            print(e)

        # if you got here, the model failed...
        enb += 1
        with open("lasterrormodel" + str(enb), "wb") as f:
            pickle.dump(model, originalmodel, mutators, file=f)
        print(model)
        return False


'''TRUTH TABLE BASED MORPHS'''
def not_morph(cons):
    con = random.choice(cons)
    ncon = ~con
    return [~ncon]
def xor_morph(cons):
    '''morph two constraints with XOR'''
    con1, con2 = random.choices(cons,k=2)
    #add a random option as per xor truth table
    return [random.choice((
        Xor([con1, ~con2]),
        Xor([~con1, con2]),
        ~Xor([~con1, ~con2]),
        ~Xor([con1, con2])))]

def and_morph(cons):
    '''morph two constraints with AND'''
    con1, con2 = random.choices(cons,k=2)
    return [random.choice((
        ~((con1) & (~con2)),
        ~((~con1) & (~con2)),
        ~((~con1) & (con2)),
        ((con1) & (con2))))]

def or_morph(cons):
    '''morph two constraints with OR'''
    con1, con2 = random.choices(cons,k=2)
    #add all options as per xor truth table
    return [random.choice((
        ((con1) | (~con2)),
        ~((~con1) | (~con2)),
        ((~con1) | (con2)),
        ((con1) | (con2))))]

def implies_morph(cons):
    '''morph two constraints with ->'''
    con1, con2 = random.choices(cons,k=2)
    #add all options as per xor truth table
    return [random.choice((
        ~((con1).implies(~con2)),
        ((~con1).implies(~con2)),
        ((~con1).implies(con2)),
        ((con1).implies(con2))))]

'''CPMPY-TRANSFORMATION MORPHS'''


def flatten_morph(cons):
    n = random.randint(1,len(cons))
    randcons = random.choices(cons,k=n)
    try:
        flatcons = flatten_constraint(randcons)
        return flatcons
    except Exception as e:
        raise Exception(flatten_constraint,randcons)


def only_numexpr_equality_morph(cons,supported=frozenset()):
    n = random.randint(1, len(cons))
    randcons = random.choices(cons, k=n)
    try:
        newcons = only_numexpr_equality(randcons, supported=supported)
        return newcons
    except Exception:
        raise Exception(only_numexpr_equality, randcons)


def normalized_boolexpr_morph(cons):
    randcon = random.choice(cons)
    try:
        con, newcons = normalized_boolexpr(randcon)
        return newcons + [con]
    except Exception:
        raise Exception(normalized_boolexpr, randcon)

def normalized_numexpr_morph(cons):
    #TODO should call this on subexpressions, so it's actually called on numexpressions as well
    randcon = random.choice(cons)
    try:
        con, newcons = normalized_numexpr(randcon)
        return newcons +[con]
    except Exception:
        raise Exception(normalized_numexpr, randcon)

def negated_normal_morph(cons):
    con = random.choice(cons)
    try:
        nncon = negated_normal(con)
        return [~nncon]
    except Exception as e:
        raise Exception(negated_normal, con)


def linearize_constraint_morph(cons):
    randcons = random.choices(cons,k=len(cons))
    #only apply linearize after flattening
    flatcons = flatten_constraint(randcons)
    try:
        lincons = linearize_constraint(flatcons)
    except Exception as e:
        raise Exception(linearize_constraint, flatcons)
    return lincons

def add_solution(cons):
    vars = get_variables(cons)
    return [var == var.value() for var in vars]

if __name__ == '__main__':
    dirname = "models"
    solver = "ortools"
    iters = 5 # number of metamorphic mutations per model
    sat = True
    enb = 0
    while enb < 10:
        fmodels = glob.glob(join(dirname, "*.bt"))
        sat = metamorphic_test(dirname, solver, iters, fmodels, enb)
        if not sat:
            enb += 1

