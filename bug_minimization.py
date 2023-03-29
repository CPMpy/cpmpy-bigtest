from cpmpy import Model
from cpmpy.transformations.get_variables import get_variables

def mes_naive(soft, hard=[], solver="ortools"):
    """
        Like MUS algorithm but in stead of looking for the model becoming sat
        we look for the solve call to not throw an error anymore
    """
    m = Model(hard + soft)
    no_error = False
    try:
        m.solve(solver=solver)
        no_error = True
    except Exception:
        pass
    if no_error:
        raise AssertionError("model should throw error during solve")

    mes = []
    # order so that constraints with many variables are tried and removed first
    core = sorted(soft, key=lambda c: -len(get_variables(c)))
    for i in range(len(core)):
        subcore = mes + core[i + 1:]  # check if all but 'i' makes core SAT

        try:
            Model(hard + subcore).solve(solver=solver)
            #removing it gives no more error, keep it
            mes.append(core[i])
        except:
            pass
    return mes