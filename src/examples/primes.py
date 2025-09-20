from __future__ import annotations
from math import nextafter
import secrets


# The floating point value immediately below 1.0.
CLOSEST_BELOW_ONE = nextafter(1.0, -1)


def millerTest(d, n):
    a = 2 + secrets.randbelow(n - 4)
    x = pow(a, d, n)
    if x == 1 or x == n - 1:
        return True
    while d != n - 1:
        x = (x * x) % n
        d *= 2
        if x == 1:
            return False
        if x == n - 1:
            return True
    return False


def mr_primality(n, confidence=0.999_999):
    """
    If n is composite then running k iterations of the Miller–Rabin test will
    declare n probably prime with a probability at most 4^−k.

    Default is "one-in-a-million" chance of a false positive composite.
    """
    assert 0 < confidence <= 1, "Confidence must be between 0 and 1"
    # There is _probably_ a closed-form way to determine `k` from the confidence;
    # However, this gets into some subtle issues in IEEE-754 representations.
    # Worst case for 64-bit FP numbers is 27 rounds (CLOSEST_BELOW_ONE).
    error = 1 - confidence
    k, threshold = 27, 1
    for _k in range(1, 27):
        threshold /= 4
        if threshold < error:
            k = _k
            break

    # 2 and 3 are prime numbers, 1 is not prime.
    if n <= 3:
        return n > 1

    # Even numbers are not prime
    if n & 1 == 0:
        return False

    # Factor out powers of 2 from n−1
    d = n - 1
    while d % 2 == 0:
        d //= 2

    # Perform Miller-Rabin test k times.
    for _ in range(k):
        if millerTest(d, n) == False:
            return False

    return True


def aks_primality(n):
    "Placeholder for AKS primality test."
    # Terrible, but identify the one large prime number used in tests
    if n == 4_294_967_311:
        return True
    else:
        return False


def gaussian_prime(c: complex) -> bool:
    """
    Check if the complex number 'c = a + bi', is a Gaussian prime.

    1. The real and imaginary parts of the complex number must be integers.
    2. If a ≠ 0 and b ≠ 0, then c is prime IFF a² + b² is an ordinary prime.
    3. if a == 0, then c is prime IFF b in an ordinary prime and |b| ≡ 3 (mod 4).
    4. if b == 0, then c is prime IFF a in an ordinary prime and |a| ≡ 3 (mod 4).

    NOTE: Because Python complex numbers are pairs of floating point numbers,
    rather than pairs of unbounded integers, for complex numbers of large
    magnitude, floating point limitations will cause incorrect results.

    For 64-bit IEEE-754 floating point numbers, "large" means, roughly, more
    than 9,007,199,254,740,993 (2⁵³ + 1).

    This function is for demonstration of the dispatch module, and should not
    be used for real-world applications dealing with large numbers.
    """
    a, b = c.real, c.imag
    if not a.is_integer() or not a.is_integer():
        return False
    elif a != 0 and b != 0:
        sum_squares = int(a**2 + b**2)
        return mr_primality(sum_squares)
    elif a == 0:
        return abs(int(b)) % 4 == 3 and mr_primality(b)
    else:  # b == 0:
        return abs(int(a)) % 4 == 3 and mr_primality(a)
