Models obtained by collecting CPMpy examples from 
https://github.com/CPMpy/cpmpy/tree/csplib and 
https://github.com/hakank/hakank/tree/master/cpmpy
from 27th september 2022

manually converting .ipynb-files to .py-files (automaticcly would also be possible using ipython and nbconvert.

After that we modify the CPMpy library to include a ```cpm_model.to_file("Pickled"+(str(time.time())).replace('.',""))``` in every solve (and solveAll) call in Model.py and adding a 
```cpm_model.to_file("Pickled"+(str(time.time())).replace('.',""))``` to all __init__ functions in all files in the "solvers" folder of CPMpy

With this temporary modified CPMpy we can start "getModels.py". Some examples may require the installation of other Python libraries, this may result in some crashes if not installed before hand.
"getModels.py" will run over all ".py" files and execute them, the modified CPMpy will output a pickled model which gets named correclty by "getModels.py".
For size reasons the models are compressed using brotli's compress, they will need to be decompressed before use. 
