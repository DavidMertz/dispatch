# Multiple and Predicative Dispatch

This module enables extensible and context-sensitive dispatch to different
code implementations that depend both on the annotated type of arguments and
on predicates that are fulfilled by arguments.

Specifically, these dispatch decisions are arranged in a manner different than
with blocks of `if/elif` or `match/case` statements, and also differently from
inheritance hierarchies that resolve to a narrowest descendant type containing
a given method.

Numerous developers have created a version of a multimethods for Python (see
the _History_ section).  Most or all of those use decorators, or other
conventions, to attach multiple implementations to the same global name, and
switch between implentations at call time within an ordinary-looking function.

I have decided here on a slightly different API.  A "dispatcher" is a
namespace in which multiple callable names may live, and calling each one
makes a runtime dispatch decision. The general intention in this design is
that these namespaces (classes, behind the scenes) can associate related
functionality, and the collection of names and implementations in a namespace
can all be imported by importing the one namespace object.

A default dispatcher named `Dispatcher` can be imported directly, but normally
a factory function will generate new ones.  In the API example below, the
namespace created is called `nums` (e.g. for numeric functions with multiple
implementations), but a real problem might create others called `strings` or
`events` or `datasets`.

The advantage of having a namespace object that maintains dispatchable
implementations is that that object itself is indefinitely extensible.  Within
your application code that imports, e.g., the `num` namespace object, you can
add many new function names and/or implementations for the already defined
names.

## API

Let's look at an example of usage that you can find in the `src/examples/`
directory of the repository.  The `confidence` argument allows us to set
a threshold for demanded certainty of the primality of large numbers.

```python
from __future__ import annotations
from math import sqrt

from dispatch.dispatch import get_dispatcher
from primes import akw_primality, mr_primality, primes_16bit
nums = get_dispatcher("nums")

@nums
def is_prime(n: int & 0 < n < 2**16) -> bool:
    "Check primes from pre-computed list"
    return n in primes_16bit

@nums
def is_prime(n: 0 < n < 2**32) -> bool:
    "Check prime factors for n < √2³²"
    ceil = sqrt(n)
    for prime in primes_16bit:
        if prime > ceil:
            return True
        if n % prime == 0:
            return False
    return True

@nums(name="is_prime")
def miller_rabin(
    n: int & n >= 2**32, 
    confidence: float = 0.999_999,
) -> bool:
    "Use Miller-Rabin pseudo-primality test"
    return mr_primality(n, confidence)

@nums(name="is_prime")
def agrawal_kayal_saxena(
    n: int & n >= 2**32,
    confidence: float & confidence == 1.0,
) -> bool:
    "Use Agrawal-Kayal-Saxena deterministic primality test"
    return aks_primality(n)

# Bind to the Gaussian prime function (which _has_ a type annotation)
nums(name="is_prime")(gaussian_prime)  

@nums
def is_twin_prime(n: int):
    "Check if n is part of a twin prime pair"
    return nums.is_prime(n) and (nums.is_prime(n + 2) or nums.is_prime(n - 2))


nums.is_prime(64_489)                        # True by direct search
nums.is_prime(64_487)                        # False by direct search
nums.is_prime(262_147)                       # True by trial division
nums.is_prime(262_143)                       # False by trial division
nums.is_prime(4_294_967_311)                 # True by Miller-Rabin test
nums.is_prime(4_294_967_309)                 # False by Miller-Rabin test
nums.is_prime(4_294_967_311, confidence=1.0) # True by AKS test
nums.is_prime(4_294_967_309, confidence=1.0) # False by AKS test
nums.is_prime(-4 + 5j)                       # True by Gaussian prime test
nums.is_prime(+4 - 7j)                       # False by Gaussian prime test
nums.is_twin_prime(617)                      # True (smaller of two)
nums.is_twin_prime(619)                      # True (larger of two)
nums.is_twin_prime(621)                      # False (not a prime)
nums.is_twin_prime(631)                      # False (not a twin)

print(nums) # -->
# nums with 2 function bound to 6 implementations (0 extra types)
nums.describe() # -->
# nums bound implementations:
# (0) is_prime
#     n: int ∩ 0 < n < 2 ** 16
# (1) is_prime
#     n: Any ∩ n < 2 ** 32
# (2) is_prime (re-bound 'miller_rabin')
#     n: int ∩ n >= 2 ** 32
#     confidence: float ∩ True
# (3) is_prime (re-bound 'agrawal_kayal_saxena')
#     n: int ∩ n >= 2 ** 32
#     confidence: float ∩ confidence == 1.0
# (0) is_twin_prime
#     n: int ∩ True

```

## History

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
implement a choice of what "MRO" to use in choosing an implementation function.
This package may or may not do that in later versions.

Way back in the early 2000s, not too long after I first wrote about and
implemented multiple dispatch in Python, a wondeful fellow Pythonista named
Phillip J Eby wrote a library called PEAK (Python Enterprise Application Kit).
Among the many things thrown into PEAK—in a manner much like how I threw every
passing thought and article into Gnosis Utilities—was a "dispatch" module:

  * https://gnosis.cx/publish/programming/charming_python_b22.html

That nifty library makes up much of the inspiration for this one.  In those
post-Python-2.4 days, when we had decorators (but before `print()` became a
function), Phillip allowed us to write things like this:

```python
import dispatch

@dispatch.generic()
def doIt(foo, other):
    "Base generic function of 'doIt()'"

@doIt.when("isinstance(foo,int) and isinstance(other,str)")
def doIt(foo, other):
    print  "foo is an unrestricted int |", foo, other

@doIt.when("isinstance(foo,int) and 3<=foo<=17 and isinstance(other,str)")
def doIt(foo, other):
    print "foo is between 3 and 17 |", foo, other

@doIt.when("isinstance(foo,int) and 0<=foo<=1000 and isinstance(other,str)")
def doIt(foo, other):
    print "foo is between 0 and 1000 |", foo, other
```        
