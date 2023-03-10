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
b = False
c = False
#c = True

#to read one of the original models: decompress as well
if c:
    #f = 'internalcrashes\\internalfunctioncrashnormalizenumexpr'
    f = 'models\\hakank-sudoku1665051085219474.bt'
    with open(f, 'rb') as fpcl:
        modle = pickle.loads(brotli.decompress(fpcl.read()))
        cons = modle.constraints
        #funct, argum, lastmodel = pickle.loads(fpcl.read())
        #print(modle.solve())
        #cons = lastmodel.constraints
        #funct(argum)

        pass

#read an internal crash, I put them in a separate folder called internalcrashes
if a:
    f = 'internalcrashes\\internalfunctioncrash1'
    #will crash when file does not exist
    for n in range(1,11):
        f = 'internalfunctioncrash' + str(n)
        with open(f, 'rb') as fpcl:
            funct,argum,lastmodel = pickle.loads(fpcl.read())
            print(funct)

#read lasterrormodel (unsat model)
elif b:
    f = 'lasterrormodel0'
    with open(f, 'rb') as fpcl:
        modle, originalmodel, mutatorsused = pickle.loads(fpcl.read())
        constraints = modle.constraint
        #checking if subset of constraints is unsat
        n = len(constraints)
        cons = constraints[:n-20]
        print(Model(cons).solve())