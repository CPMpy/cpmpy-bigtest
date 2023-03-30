import brotli
import glob
import pickle
from os.path import join

from cpmpy import Table

import cpmpy as cp
from cpmpy.expressions.python_builtins import any
from mutators import *


def lists_to_conjunction(cons):
    # recursive...
    return [any(lists_to_conjunction(c)) if is_any_list(c) else c for c in cons]


def metamorphic_test(dirname, solver, iters,fmodels,enb,limit):
    #list of mutators and the amount of constraints they accept.
    mm_mutators = [xor_morph, and_morph, or_morph, implies_morph, not_morph,
                   negated_normal_morph,
                   linearize_constraint_morph,
                   flatten_morph,
                   only_numexpr_equality_morph,
                   normalized_numexpr_morph,
                   reify_rewrite_morph,
                   only_bv_implies_morph,
                   only_var_lhs_morph,
                   only_const_rhs_morph,
                   only_positive_bv_morph,
                   flat2cnf_morph,
                   toplevel_list_morph,
                   decompose_globals_morph,
                   semanticFusion]
    #mm_mutators = [normalized_numexpr_morph]
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
        solutionTable = []
        originalvariables = get_variables(cons)
        nbSolutions = cp.Model(cons).solveAll(solver=solver,display=lambda: solutionTable.append([x == x.value() for x in originalvariables]), solution_limit=limit)
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
                filename = "internalfunctioncrash_tab"+str(enb)+".pickle"
                with open(filename, "wb") as ff:
                    pickle.dump([function, argument, originalmodel, e], file=ff) # log function and arguments that caused exception
                print('IE', end='', flush=True)
                return False # no need to solve model we didn't modify..


        # enough mutations, time for solving
        r = True
        for i in range(nbSolutions):
            try:
                model = cp.Model(cons + solutionTable[i])
                sat = model.solve(solver=solver)
                if model.status().runtime > 15:
                    # timeout, skip
                    print('s', end='', flush=True)
                    return True
                elif sat:
                    pass
                    # has to be SAT...
                    #print('.', end='', flush=True)
                else:
                    print('X', end='', flush=True)
                    print('morphs: ', mutators)
                    r = False
            except Exception as e:
                print('E', end='', flush=True)
                print(e)
                r = False
            if not r:
                # if you got here, the model failed...
                enb += 1
                with open("lasterrormodel_tab" + str(enb)+".pickle", "wb") as f:
                    pickle.dump([model, originalmodel, mutators], file=f)
            #print(model)
                return False
        if r:
            print('.', end='', flush=True)
            return r


if __name__ == '__main__':
    dirname = "models"
    solver = "ortools"
    iters = 5 # number of metamorphic mutations per model
    limit = 10 #max number of solutions to look for (just to make it time-feasible)
    sat = True
    enb = 0

    random.seed(0)
    while enb < 10:
        fmodels = glob.glob(join(dirname, "*.bt"))
        sat = metamorphic_test(dirname, solver, iters, fmodels, enb,limit)
        if not sat:
            enb += 1

