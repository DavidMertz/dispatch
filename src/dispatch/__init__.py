HISTORY = """
I once implemented multiple dispatch (multimethods) in an ancient 2002 package:

  * https://pypi.org/project/Gnosis_Utils/
  * https://gnosis.cx/download/gnosis/magic/multimethods.py

DON'T USE THAT!

It might not work with anything after Python 2.3.  And even if it does, it's
certainly not an elegant API for modern Python (it came before decorators or
annotations, for example).

My article from the time is still basically correct and useful:

  * https://gnosis.cx/publish/programming/charming_python_b12.html

A great many other people have also implemented multiple dispatch (usually with
the name "multimethods") in Python.  See https://pypi.org/search/?q=multimethods
for many of these libraries.  

These implementations are probably all perfectly fine.  I haven't tried most of
them, and the authors might make somewhat different choices about APIs than I do
here.  But I'm sure that almost all of them work well.

One thing I did, back in 2002 that no one else seems to have done, is to
implement a choice of what "MRO" to use is choosing an implementation function.
This package may or may not do that in later versions.

Way back in the early 2000s, not too long after I first wrote about and
implemented multiple dispatch in Python, a wondeful fellow Pythonista named
Phillip J Eby wrote a library called PEAK (Python Enterprise Application Kit).
Among the many things thrown into PEAK—in a manner much like how I threw every
passing though and article into Gnosis Utilities—was a "dispatch" module:

  * https://gnosis.cx/publish/programming/charming_python_b22.html

That nifty library makes up much of the inspiration for this one.  In those
post-Python-2.4 days, when we had decorators (but before `print()` became a
function), Phillip allowed us to write things like this:

    import dispatch

    @dispatch.generic()
    def doIt(foo, other):
        "Base generic function of 'doIt()'"

    @doIt.when("isinstance(foo,int) and isinstance(other,str)")
    def doIt(foo, other):
        print "foo is an unrestricted int |", foo, other

    @doIt.when("isinstance(foo,int) and 3<=foo<=17 and isinstance(other,str)")
    def doIt(foo, other):
        print "foo is between 3 and 17 |", foo, other

    @doIt.when("isinstance(foo,int) and 0<=foo<=1000 and isinstance(other,str)")
    def doIt(foo, other):
        print "foo is between 0 and 1000 |", foo, other
"""

