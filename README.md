# Multiple and Predicative Dispatch

This package enables extensible and context-sensitive dispatch to different
code implementations that depend both on the annotated type of arguments and
on predicates that are fulfilled by arguments.

Specifically, these dispatch decisions are arranged in a manner different than
with blocks of `if/elif` or `match/case` statements, and also differently from
inheritance hierarchies that resolve to a narrowest descendant type containing
a given method.  

This approach is often better than other paradigms both because of the clarity
of implementation signatures and because of its flexible and simple
extensibility.

A "dispatcher" is a namespace in which multiple callable names may live, and
calling each one makes a runtime dispatch decision. These namespaces (classes,
behind the scenes) can associate related functionality, and the collection of
names and implementations in a namespace can all be imported by importing the
one namespace object.

A default dispatcher named `Dispatcher` can be imported directly, but normally
a factory function will generate new ones. The advantage of having a namespace
object that maintains dispatchable implementations is that that object itself
is indefinitely extensible.  

## Usage Example

In the API example below, the namespace created is called `nums` (e.g. for
numeric functions with multiple implementations), but you can equally create
others called, e.g. `events` or `datasets` or `customers`. A full application
might utilize many namespace objects.

Within your application code that imports, e.g., the `num` namespace object,
you can add many new function names and/or implementations for the already
defined names.

```python
from __future__ import annotations
from math import sqrt

from dispatch.dispatch import get_dispatcher
from primes import akw_primality, mr_primality, primes_16bit
nums = get_dispatcher("Numbers")

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

print(nums) # -->
# Numbers with 2 function bound to 6 implementations (0 extra types)
nums.describe() # -->
# Numbers bound implementations:
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
```
