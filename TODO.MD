Clean up code
	comments
	removal of desktop-path and co
change to ask for a solver (no solver = all solvers)
one call of main function is on one solver, one model, X transformations (easier to debug)
change exisitng transforamtions to be individual functions
add transformations
	... & True
	... | Not ...
	truth table level
	c1 & c2
	~(c1 & ~c2)
	~(~c1 & c2)
	~(~c1 & ~c2)
	c1 == c2
	~(c1 == ~c2)
	~(~c1 == c2)
	~c1 == ~c2
	and others
Document how to run