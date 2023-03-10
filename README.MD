Repository for the future testing of CPMpy with the use of differential testing and metamorphic testing.
It also will contain a tool to reduce the model in case a bug is found and a way to obtain CPMpy models to test CPMpy using the two techniques above.



This repository builds futher on the work of the thesis by Ruben Kindt which was under guidance of Tias Guns and Ignace Bleukx.

If an error is found in an internal function, a file with the name internalfunctioncrash will be created, containing 
function, argument, originalmodel that cause the error.

If a model becomes unsat after transformations, a file with the name lasterrormodel is created, containing 
model (the unsat model), originalmodel, mutators (list of mutators that were used)

This files can be read by using pickle.load, as you can see in the example code in errorexploration.py