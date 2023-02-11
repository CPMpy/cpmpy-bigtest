Models are collected by running a slightly modified version of CPMpy, which stores (pickles) the models that are given to a solver.

(this covers both the case of a generic `model.solve()` call, as well as of a specific `model.solve("mysolver")` call)

## Patch

See patch included.

We also compressed them post-hoc with 'brotli' to save diskspace, code not included...


## Scripts

Also some helper scripts to detect unsat models, and to identify too slow models for inclusion in the testsuite, as well as removing structurally likely-similar models.
