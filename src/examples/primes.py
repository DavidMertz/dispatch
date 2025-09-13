from math import nextafter
import random
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
    k = 27
    for _k in range(1, 27):
        if 4 ** (-1 * _k) < error:
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
    # TODO: Implement AKS primality test.
    return random.choice([bool(n), False])
