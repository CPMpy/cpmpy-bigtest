import random
from cpmpy import intvar
from cpmpy.expressions.core import Expression, Operator
from cpmpy.transformations.get_variables import get_variables
from cpmpy.transformations.linearize import linearize_constraint
from cpmpy.expressions.utils import is_any_list, is_boolexpr
from cpmpy.transformations.flatten_model import flatten_constraint, normalized_boolexpr, normalized_numexpr, \
    negated_normal
from cpmpy.transformations.reification import only_bv_implies, reify_rewrite
from cpmpy.transformations.comparison import only_numexpr_equality
from cpmpy.expressions.globalconstraints import Xor


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
    '''normalized_boolexpr only gets called within other transformations, so can probably safely be omitted from our test.
    Keeping it in gives unwanted results, for example crashing on flatvar input'''
    randcon = random.choice(cons)
    try:
        con, newcons = normalized_boolexpr(randcon)
        return newcons + [con]
    except Exception as e:
        raise MetamorphicError(normalized_boolexpr, randcon, e)

def normalized_numexpr_morph(cons):
    random.shuffle(cons)
    firstcon = None
    for i, con in enumerate(cons):
        res = pickaritmetic(con, log=[i])
        if res != []:
            firstcon = random.choice(res)
            break #numexpr found
    if firstcon is None:
        #no numexpressions found but still call the function to test on all inputs
        randcon = random.choice(cons)
        try:
            con, newcons = normalized_numexpr(randcon)
            return cons + newcons + [con]
        except Exception as e:
            raise MetamorphicError(normalized_numexpr, randcon, e)
    else:
        #get the numexpr
        arg = cons[firstcon[0]]
        newfirst = arg
        for i in firstcon[1:]:
            arg = arg.args[i]
        firstexpr = arg
        try:
            con, newcons = normalized_numexpr(firstexpr)
        except Exception as e:
            raise MetamorphicError(normalized_numexpr, firstexpr, e)

        # make the new constraint (newfirst)
        arg = newfirst
        c = 1
        for i in firstcon[1:]:
            c += 1
            if c == len(firstcon):
                arg.args[i] = con
            else:
                arg = arg.args[i]

        return cons + [newfirst] + newcons
def negated_normal_morph(cons):
    con = random.choice(cons)
    try:
        return [~negated_normal(con)]
    except Exception as e:
        raise MetamorphicError(negated_normal, con, e)


def linearize_constraint_morph(cons):
    n = random.randint(1, len(cons))
    randcons = random.choices(cons, k=n)
    #only apply linearize after flattening
    flatcons = flatten_morph(randcons, flatten_all=True)
    try:
        return linearize_constraint(flatcons)
    except Exception as e:
        raise MetamorphicError(linearize_constraint, flatcons, e)

def reify_rewrite_morph(cons):
    n = random.randint(1, len(cons))
    randcons = random.choices(cons, k=n)
    #only apply linearize after flattening
    flatcons = flatten_morph(randcons, flatten_all=True)
    try:
        return reify_rewrite(flatcons)
    except Exception as e:
        raise MetamorphicError(reify_rewrite, flatcons, e)


def only_bv_implies_morph(cons):
    n = random.randint(1, len(cons))
    randcons = random.choices(cons, k=n)
    #only apply linearize after flattening
    flatcons = flatten_morph(randcons, flatten_all=True)
    try:
        return only_bv_implies(flatcons)
    except Exception as e:
        raise MetamorphicError(only_bv_implies, flatcons, e)

#decompose_globals()

def add_solution(cons):
    vars = get_variables(cons)
    return [var == var.value() for var in vars if var.value() is not None]


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
            firstexpr, secondexpr = z - secondexpr, z - firstexpr

            #make the new constraints
            arg = newfirst
            c = 1
            for i in firstcon[1:]:
                c+=1
                if c == len(firstcon):
                    if isinstance(arg.args, tuple):
                        arg.args = list(arg.args)
                    arg.args[i] = firstexpr
                else:
                    arg = arg.args[i]

            arg = newsecond
            c = 1
            for i in secondcon[1:]:
                c += 1
                if c == len(secondcon):
                    if isinstance(arg.args, tuple):
                        arg.args = list(arg.args)
                    arg.args[i] = secondexpr
                else:
                    arg = arg.args[i]

            return cons + [newfirst,newsecond]

        else:
            #no expressions found to fuse
            return cons

    except Exception as e:
        raise MetamorphicError(semanticFusion, cons, e)

class MetamorphicError(Exception):
    pass

'''
returns a list of aritmetic expressions that occur in the input expression. 
One (random) candidate is taken from each level of the expression if there exists one '''
def pickaritmetic(con,log=[], candidates=[]):
    if hasattr(con,'name'):
        if con.name == 'wsum':
            #wsum has lists as arguments so we need a separate case
            #wsum is the lowest possible level
            return candidates + [log]
        if con.name == "element" or con.name == "table":
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
