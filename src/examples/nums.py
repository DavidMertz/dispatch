from __future__ import annotations
from math import sqrt
from dispatch.dispatch import get_dispatcher
from examples.primes import (
    aks_primality as agrawal_kayal_saxena,
    gaussian_prime,
    mr_primality as miller_rabin_prime,
)
from examples.data import  primes_16bit

def is_small_prime(n: int) -> bool:
    return n in primes_16bit

def is_medium_prime(n: int) -> bool:    
    ceil = sqrt(n)
    for prime in primes_16bit:
        if prime > ceil:
            return True
        if n % prime == 0:
            return False
    return True

nums = get_dispatcher("nums")
@nums
def is_prime(n: int & 0 < n < 2**16) -> bool:  # type: ignore
    return is_small_prime(n)

@nums
def is_prime(n: 0 < n < 2**32) -> bool:  # type: ignore
    return is_medium_prime(n)

@nums(name="is_prime")
def mr_prime(n: int & n >= 2**32,  # type: ignore
             confidence: float = 0.999_999):
    return miller_rabin_prime(n, confidence)

@nums(name="is_prime")
def aks_prime(n: int & n >= 2**32,  # type: ignore
              confidence: float & confidence == 1.0):  # type: ignore
    _ = confidence
    return agrawal_kayal_saxena(n)

# Gaussian prime is already annotated as ‘n: complex’
nums(name="is_prime")(gaussian_prime)

@nums
def is_twin_prime(n: int):
    "Check if n is part of a twin prime pair"
    return (nums.is_prime(n) and 
      (nums.is_prime(n + 2) or nums.is_prime(n - 2)))

