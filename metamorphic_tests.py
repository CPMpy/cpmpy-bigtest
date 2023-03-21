import brotli
import glob
import os
import pickle
import time
from os.path import join
import argparse
import random

from cpmpy import intvar

from cpmpy.expressions.core import Expression, Operator

from cpmpy.transformations.get_variables import get_variables

from cpmpy.transformations.linearize import linearize_constraint

import cpmpy as cp
from cpmpy.expressions.utils import is_any_list, is_boolexpr
from cpmpy.transformations.flatten_model import flatten_constraint, normalized_boolexpr, normalized_numexpr, \
    negated_normal
from cpmpy.transformations.reification import only_bv_implies, reify_rewrite
from cpmpy.transformations.comparison import only_numexpr_equality

from cpmpy.expressions.globalconstraints import Xor


def lists_to_conjunction(cons):
    # recursive...
    return [any(lists_to_conjunction(c)) if is_any_list(c) else c for c in cons]


def metamorphic_test(dirname, solver, iters,fmodels,enb):
    #list of mutators and the amount of constraints they accept.
    mm_mutators = [xor_morph, and_morph, or_morph, implies_morph, not_morph,
                   negated_normal_morph,
                   linearize_constraint_morph,
                   flatten_morph,
                   only_numexpr_equality_morph,
                   normalized_numexpr_morph,
                   normalized_boolexpr_morph,
                   reify_rewrite_morph,
                   only_bv_implies_morph,
                   add_solution]
    mm_mutators = [semanticFusion]
    # choose a random model
    f = random.choice(fmodels)
    originalmodel = f
    with open(f, 'rb') as fpcl:
        cons = pickle.loads(brotli.decompress(fpcl.read())).constraints
        assert (len(cons)>0), f"{f} has no constraints"
        # replace lists by conjunctions
        cons = lists_to_conjunction(cons)
        assert (len(cons)>0), f"{f} has no constraints after l2conj"
        assert (cp.Model(cons).solve()), f"{f} is not sat"
        mutators = []
        for i in range(iters):
            # choose a metamorphic mutation
            m = random.choice(mm_mutators)
            # an error can occur in the transformations, so even before the solve call.
            # log function and arguments in that case
            mutators += [m]
            try:
                cons += m(cons)  # apply a metamorphic mutation
            except MetamorphicError as exc:
                enb += 1
                function, argument, e = exc.args
                filename = "internalfunctioncrash"+str(enb)+".pickle"
                with open(filename, "wb") as ff:
                    pickle.dump([function, argument, originalmodel, e], file=ff) # log function and arguments that caused exception
                print('IE', end='', flush=True)
                return False # no need to solve model we didn't modify..


        # enough mutations, time for solving
        try:
            model = cp.Model(cons)
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
        with open("lasterrormodel" + str(enb)+".pickle", "wb") as f:
            pickle.dump([model, originalmodel, mutators], file=f)
        #print(model)
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
    try:
        #add all options as per xor truth table
        return [random.choice((
            ~((con1).implies(~con2)),
            ((~con1).implies(~con2)),
            ((~con1).implies(con2)),
            ((con1).implies(con2))))]
    except Exception as e:
        raise MetamorphicError(implies_morph,cons,e)

'''CPMPY-TRANSFORMATION MORPHS'''


def flatten_morph(cons, flatten_all=False):
    if flatten_all is False:
        n = random.randint(1,len(cons))
        randcons = random.choices(cons,k=n)
    else:
        randcons = cons
    try:
        flatcons = flatten_constraint(randcons)
        return flatcons
    except Exception as e:
        raise MetamorphicError(flatten_constraint,randcons, e)


def only_numexpr_equality_morph(cons,supported=frozenset()):
    n = random.randint(1, len(cons))
    randcons = random.choices(cons, k=n)
    flatcons = flatten_morph(randcons, flatten_all=True) # only_numexpr_equality requires flat constraints
    try:
        newcons = only_numexpr_equality(flatcons, supported=supported)
        return newcons
    except Exception as e:
        raise MetamorphicError(only_numexpr_equality, flatcons, e)


def normalized_boolexpr_morph(cons):
    randcon = random.choice(cons)
    try:
        con, newcons = normalized_boolexpr(randcon)
        return newcons + [con]
    except Exception as e:
        raise MetamorphicError(normalized_boolexpr, randcon, e)

def normalized_numexpr_morph(cons):
    #TODO should call this on subexpressions, so it's actually called on numexpressions as well
    randcon = random.choice(cons)
    try:
        con, newcons = normalized_numexpr(randcon)
        return newcons +[con]
    except Exception as e:
        raise MetamorphicError(normalized_numexpr, randcon, e)

def negated_normal_morph(cons):
    con = random.choice(cons)
    try:
        return [~negated_normal(con)]
    except Exception as e:
        raise MetamorphicError(negated_normal, con, e)


def linearize_constraint_morph(cons):
    randcons = random.choices(cons,k=len(cons))
    #only apply linearize after flattening
    flatcons = flatten_morph(randcons, flatten_all=True)
    try:
        return linearize_constraint(flatcons)
    except Exception as e:
        raise MetamorphicError(linearize_constraint, flatcons, e)

def reify_rewrite_morph(cons):
    randcons = random.choices(cons,k=len(cons))
    #only apply linearize after flattening
    flatcons = flatten_morph(randcons, flatten_all=True)
    try:
        return reify_rewrite(flatcons)
    except Exception as e:
        raise MetamorphicError(reify_rewrite, flatcons, e)


def only_bv_implies_morph(cons):
    randcons = random.choices(cons,k=len(cons))
    #only apply linearize after flattening
    flatcons = flatten_morph(randcons, flatten_all=True)
    try:
        return only_bv_implies(flatcons)
    except Exception as e:
        raise MetamorphicError(only_bv_implies, flatcons, e)

def add_solution(cons):
    vars = get_variables(cons)
    return [var == var.value() for var in vars]


def semanticFusion(cons):
    try:
        firstcon = None
        secondcon = None
        random.shuffle(cons)
        for i, con in enumerate(cons):
            res = pickaritmetic(con,log=[i])
            if res != []:
                if firstcon == None:
                    firstcon = random.choice(res)
                elif secondcon == None:
                    secondcon = random.choice(res)
                    break #stop when 2 constraints found. still random because cons are shuffled

        if secondcon != None:
            #two constraints with aritmetic expressions found, perform semantic fusion on them
            #get the expressions to fuse
            arg = cons[firstcon[0]]
            newfirst = arg
            for i in firstcon[1:]:
                arg = arg.args[i]
            firstexpr = arg

            arg = cons[secondcon[0]]
            newsecond = arg
            for i in secondcon[1:]:
                arg = arg.args[i]
            secondexpr = arg

            lb,ub = Operator('sum',[firstexpr,secondexpr]).get_bounds()
            z = intvar(lb, ub)
            if is_any_list(firstexpr) or is_any_list(secondexpr):
                print('bugged')
                pass
            firstexpr, secondexpr = z - secondexpr, z - firstexpr

            #make the new constraints
            arg = newfirst
            c = 1
            for i in firstcon[1:]:
                c+=1
                if c == len(firstcon):
                    arg.args[i] = firstexpr
                else:
                    arg = arg.args[i]

            arg = newsecond
            c = 1
            for i in secondcon[1:]:
                c += 1
                if c == len(secondcon):
                    arg.args[i] = secondexpr
                else:
                    arg = arg.args[i]

            return cons + [newfirst,newsecond]

        else:
            #no expressions found to fuse
            return cons

    except Exception as e:
        raise MetamorphicError(semanticFusion, cons, e)

'''
returns a list of aritmetic expressions that occur in the input expression. 
One (random) candidate is taken from each level of the expression if there exists one '''
def pickaritmetic(con,log=[], candidates=[]):
    if hasattr(con,'name'):
        if con.name == 'wsum':
            #wsum has lists as arguments so we need a separate case
            #wsum is the lowest possible level
            return candidates + [log]
        if con.name == "element":
            #no good way to know if element will return bool or not so ignore it (lists and element always return false to isbool)
            return candidates
    if hasattr(con, "args"):
        iargs = [(j, e) for j, e in enumerate(con.args)]
        random.shuffle(iargs)
        for j, arg in iargs:
            if is_boolexpr(arg):
                res = pickaritmetic(arg,log+[j])
                if res != []:
                    return res
            else:
                return pickaritmetic(arg,log+[j],candidates+[log+[j]])

    return candidates

'''def semanticFusionIntInt(satModel, operation, invOperation):
    newcons = []
    firstCons = None
    secCons = None

    for i, cons in enumerate(satModel.modifModel.constraints):
        if firstCons is None and hasattr(cons, "args"):
            if (isinstance(cons.args[0], variables._IntVarImpl) or isinstance(cons.args[0], variables._NumVarImpl)):
                firstCons = cons
                continue
        elif secCons is None and firstCons is not None and hasattr(cons, "args"):
            if (isinstance(cons.args[0], variables._IntVarImpl) or isinstance(cons.args[0], variables._NumVarImpl)):
                secCons = cons
                continue
        newcons += [cons]

    if secCons is None:
        return newcons

    x = firstCons.args[0]
    y = secCons.args[0]
    # can be written with python build-in max and min, but those are overwritten by CPMpy,
    # writing this is easier then looking up how to use the overwritten build-ins
    maxLb = operation(x.lb, y.lb) if operation(x.lb, y.lb) > operation(x.ub, y.ub) else operation(x.ub, y.ub)
    minUb = operation(x.lb, y.lb) if operation(x.lb, y.lb) < operation(x.ub, y.ub) else operation(x.ub, y.ub)
    try:
        z = intvar(lb=maxLb, ub=minUb, name=("i" + str(random.randint(0,1000))))
    except Exception as e:
        return newcons
    xr = invOperation(z, y)
    yr = invOperation(z, x)
    firstCons.args[0] = xr
    secCons.args[0] = yr
    newcons += [(firstCons) & (secCons)]

    # replace some X, Y by xr, yr
    # for j, cons in enumerate(newcons): # could cause cyclic expressions
    #     if hasattr(cons, "args"):
    #         for i, arg in enumerate(cons.args):
    #             if hasattr(arg, "name") and arg.name == x.name and random.random() < 0.5:
    #                 cons.args[i] = xr
    #             if hasattr(arg, "name") and arg.name == y.name and random.random() < 0.5:
    #                 cons.args[i] = yr
    return newcons
'''

class MetamorphicError(Exception):
    pass

if __name__ == '__main__':
    dirname = "models"
    solver = "ortools"
    iters = 5 # number of metamorphic mutations per model
    sat = True
    enb = 0

    random.seed(0)
    while enb < 10:
        fmodels = glob.glob(join(dirname, "*.bt"))
        sat = metamorphic_test(dirname, solver, iters, fmodels, enb)
        if not sat:
            enb += 1

