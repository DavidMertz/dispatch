from __future__ import annotations
from math import sqrt

from dispatch.dispatch import get_dispatcher
from examples.primes import mr_primality
from examples.data import primes_16bit
  
nums = get_dispatcher()

@nums
def is_prime(n: int & 0 < n < 2**16) -> bool:  # type: ignore
    "Check primes from pre-computed list"
    return n in primes_16bit

@nums
def is_prime(n: n < 2**32) -> bool:  # type: ignore
    "Check for prime factors < sqrt(2**32)"
    for prime in primes_16bit:
        if prime > sqrt(n):
            return True
        if n % prime == 0:
            return False
    return True

@nums(name="is_prime")
def miller_rabin(n: int & n >= 2**32):  # type: ignore
    "Use Miller-Rabin pseudo-primality test"
    return mr_primality(n)

print(nums)
print(repr(nums))
