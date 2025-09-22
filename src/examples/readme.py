from __future__ import annotations
from math import sqrt

from dispatch.dispatch import get_dispatcher
from examples.data import primes_16bit
from examples.primes import aks_primality, gaussian_prime, mr_primality

nums = get_dispatcher("nums")


@nums(name="is_prime")
def is_tiny_prime(n: int & 0 < n < 2**16) -> bool:  # type: ignore
    "Check primes from pre-computed list"
    return n in primes_16bit


@nums
def is_prime(n: 0 < n < 2**32) -> bool:  # type: ignore
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
    n: int & n >= 2**32,  # type: ignore
    confidence: float = 0.999_999,
) -> bool:
    "Use Miller-Rabin pseudo-primality test"
    return mr_primality(n, confidence)


@nums(name="is_prime")
def agrawal_kayal_saxena(
    n: int & n >= 2**32,  # type: ignore
    confidence: float & confidence == 1.0,  # type: ignore
) -> bool:
    "Use Agrawal-Kayal-Saxena deterministic primality test"
    _ = confidence  # type: ignore
    return aks_primality(n)


nums(name="is_prime")(gaussian_prime)  # Bind to the Gaussian prime function


@nums
def is_twin_prime(n: int):
    "Check if n is part of a twin prime pair"
    return nums.is_prime(n) and (nums.is_prime(n + 2) or nums.is_prime(n - 2))


print(nums)  # -->
# nums with 2 function bound to 6 implementations (0 extra types)"
nums.describe()  # -->
# nums bound implementations:
# (0) is_prime (re-bound 'is_tiny_prime')
#     n: int ∩ 0 < n < 2 ** 16
# (1) is_prime
#     n: Any ∩ n < 2 ** 32
# (2) is_prime (re-bound 'miller_rabin')
#     n: int ∩ n >= 2 ** 32
#     confidence: float ∩ True
# (3) is_prime (re-bound 'agrawal_kayal_saxena')
#     n: int ∩ n >= 2 ** 32
#     confidence: float ∩ confidence == 1.0
# (4) is_prime (re-bound 'gaussian_prime')
#     c: complex ∩ True
# (0) is_twin_prime
#     n: int ∩ True


print(f"Tiny {nums.is_prime(64_489)=}")  # True by direct search
print(f"Tiny {nums.is_prime(64_487)=}")  # False by direct search
print(f"Small {nums.is_prime(262_147)=}")  # True by trial division
print(f"Small {nums.is_prime(262_143)=}")  # False by trial division
print(f"Fuzzy {nums.is_prime(4_294_967_311)=}")  # True by Miller-Rabin test
print(f"Fuzzy {nums.is_prime(4_294_967_309)=}")  # False by Miller-Rabin test
print(f"Definite {nums.is_prime(4_294_967_311, confidence=1.0)=}")  # True by AKS test
print(f"Definite {nums.is_prime(4_294_967_309, confidence=1.0)=}")  # False by AKS test
print(f"Gaussian {nums.is_prime(-4 + 5j)=}")  # True by Gaussian prime test
print(f"Gaussian {nums.is_prime(+4 - 7j)=}")  # False by Gaussian prime test
print(f"Twin {nums.is_twin_prime(617)=}")  # True (smaller of two)
print(f"Twin {nums.is_twin_prime(619)=}")  # True (larger of two)
print(f"Twin {nums.is_twin_prime(621)=}")  # False (not a prime)
print(f"Twin {nums.is_twin_prime(631)=}")  # False (not a twin)
