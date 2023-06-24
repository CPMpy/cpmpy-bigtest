"""
Tests all models in the `models/` folder, which are known to be SAT

Will only run solver tests on solvers that are installed
"""
from glob import glob
from os.path import join
import pytest
import pickle
import brotli  # install it
from cpmpy import *
from cpmpy.transformations.flatten_model import flatten_model
from cpmpy.exceptions import NotSupportedError, TransformationNotImplementedError


MODELS = sorted(glob(join("models", "*.bt")))  # TODO .pcl.bt
# The following instances are excluded due to Exact requiring too much memory:
excluded = ["hidato_table","miss_manners16650494454778237.bt","nonogram_regular_table1665051080465427.bt", "pentonomies", "run_nonogram","stable_marriage16650508872192633.bt"]
MODELS = [x for x in MODELS if all(not x.startswith("models/"+y) for y in excluded)]

@pytest.mark.parametrize("fmodel", MODELS)
def test_model(fmodel, solver="exact"):
    """Loads model file and executes (with given solver)

    Args:
        fmodel ([string]): filename of picled brotli compressed file
        solver (string): None=use default, otherwise the named solver
    """
    with open(fmodel, 'rb') as fpcl:
        model = pickle.loads(brotli.decompress(fpcl.read()))
        try:
            sat = model.solve(solver=solver, time_limit=120)

            if model.status().runtime > 110:
                pytest.skip(f"Timeout of {fmodel}: {model.status()}")

            assert (sat), f"Model {fmodel} should be SAT"
        except (NotImplementedError,NotSupportedError,TransformationNotImplementedError):
            pytest.skip(f"{fmodel}: Not Implemented/Supported")
