import brotli
import glob
import pickle
from os.path import join
import cpmpy as cp
from cpmpy.expressions.python_builtins import any
from mutators import *


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
                   reify_rewrite_morph,
                   only_bv_implies_morph,
                   only_var_lhs_morph,
                   only_const_rhs_morph,
                   only_positive_bv_morph,
                   flat2cnf_morph,
                   toplevel_list_morph,
                   decompose_globals_morph,
                   add_solution,
                   semanticFusion]
    #mm_mutators = [aritmetic_comparison_morph]
    #mm_mutators = [only_var_lhs_morph,only_const_rhs_morph,only_positive_bv_morph,flat2cnf_morph,toplevel_list_morph]
    # choose a random model
    f = random.choice(fmodels)
    originalmodel = f
    with open(f, 'rb') as fpcl:
        model = pickle.loads(brotli.decompress(fpcl.read()))
        cons = model.constraints
        assert (len(cons)>0), f"{f} has no constraints"
        # replace lists by conjunctions
        cons = lists_to_conjunction(cons)
        assert (len(cons)>0), f"{f} has no constraints after l2conj"
        objective = model.objective_
        mininimize = model.objective_is_min
        model = cp.Model(cons)
        if mininimize:
            model.minimize(objective)
        else:
            model.maximize(objective)
        assert (model.solve()), f"{f} is not sat"
        value_before = model.objective_value() #store objective value to compare after transformations
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
                filename = "internalfunctioncrash_opt"+str(enb)+".pickle"
                with open(filename, "wb") as ff:
                    pickle.dump([function, argument, originalmodel, e], file=ff) # log function and arguments that caused exception
                print('IE', end='', flush=True)
                print(function)
                return False # no need to solve model we didn't modify..


        # enough mutations, time for solving
        try:
            newModel = cp.Model(cons)
            if mininimize:
                newModel.minimize(objective)
            else:
                newModel.maximize(objective)

            sat = newModel.solve(solver=solver, time_limit=20)
            if newModel.status().runtime > 15:
                # timeout, skip
                print('s', end='', flush=True)
                return True
            elif newModel.objective_value() != value_before:
                #objective value changed
                print('c', end='', flush=True)
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
        with open("lasterrormodel_opt" + str(enb)+".pickle", "wb") as f:
            pickle.dump([newModel, originalmodel, mutators], file=f)
        #print(model)
        return False


if __name__ == '__main__':
    dirname = "models\\optimization problems"
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

