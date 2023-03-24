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
from cpmpy.transformations.flatten_model import flatten_constraint, normalized_boolexpr, normalized_numexpr, \
    negated_normal
from cpmpy.transformations.reification import only_bv_implies, reify_rewrite
from cpmpy.transformations.comparison import only_numexpr_equality
from metamorphic_tests import *
a = False
#a = True
b = False
#b = True
c = False
#c = True

#to read one of the original models: decompress as well
if c:
    #f = 'internalcrashes\\internalfunctioncrashnormalizenumexpr'
    f = 'models\\4_marco-mus-mcs-enumeration1665051222590934.bt'
    with open(f, 'rb') as fpcl:
        modle = pickle.loads(brotli.decompress(fpcl.read()))
        cons = modle.constraints
        print(modle.solve())

#read an internal crash
if a:
    f = 'internalfunctioncrash5.pickle'
    with open(f, 'rb') as fpcl:
        funct,argum,lastmodel,e = pickle.loads(fpcl.read())
        funct(argum)

#read lasterrormodel (unsat model)
elif b:
    f = 'lasterrormodel1.pickle'
    with open(f, 'rb') as fpcl:
        modle, originalmodel, mutatorsused = pickle.loads(fpcl.read())
        #redoing mutations on orignal model
        with open(originalmodel, 'rb') as fpcl2:
            cons = pickle.loads(brotli.decompress(fpcl2.read())).constraints
        cons = lists_to_conjunction(cons)
        for mut in mutatorsused:
            cons = mut(cons)
        #checking if subset of constraints is unsat
        constraints = modle.constraints
        n = len(constraints)
        constr = constraints[:n-20]
        print(Model(constr).solve())