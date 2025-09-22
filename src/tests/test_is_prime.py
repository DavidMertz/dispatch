from __future__ import annotations
from math import sqrt

import pytest

from examples.data import primes_16bit
from examples.primes import aks_primality, mr_primality
from examples.readme import nums


@pytest.fixture(autouse=True)
def capsys(capsys):
    return capsys


def is_tiny_prime(n, confidence=1.0) -> bool:
    _ = confidence  # type: ignore
    return n in primes_16bit


def is_small_prime(n, confidence=1.0) -> bool:
    _ = confidence  # type: ignore
    ceil = sqrt(n)
    for prime in primes_16bit:
        if prime > ceil:
            return True
        if n % prime == 0:
            return False
    return True


def test_nums_str():
    assert (
        str(nums) == "nums with 2 functions bound to 6 implementations (0 extra types)"
    )


def test_nums_describe(capsys):
    expected = (
        "nums bound implementations:\n"
        "(0) is_prime (re-bound 'is_tiny_prime')\n"
        "    n: int ∩ 0 < n < 2 ** 16\n"
        "(1) is_prime\n"
        "    n: Any ∩ 0 < n < 2 ** 32\n"
        "(2) is_prime (re-bound 'miller_rabin')\n"
        "    n: int ∩ n >= 2 ** 32\n"
        "    confidence: float ∩ True\n"
        "(3) is_prime (re-bound 'agrawal_kayal_saxena')\n"
        "    n: int ∩ n >= 2 ** 32\n"
        "    confidence: float ∩ confidence == 1.0\n"
        "(4) is_prime (re-bound 'gaussian_prime')\n"
        "    c: complex ∩ True\n"
        "(0) is_twin_prime\n"
        "    n: int ∩ True\n"
    )
    nums.describe()
    out, _err = capsys.readouterr()
    assert out == expected


@pytest.mark.parametrize(
    "n, result",
    [
        (64_489, True),
        (64_487, False),
    ],
)
def test_is_tiny_prime(n, result):
    assert is_tiny_prime(n) == result


@pytest.mark.parametrize(
    "n, result",
    [
        (262_147, True),
        (262_143, False),
    ],
)
def test_is_small_prime(n, result):
    assert is_small_prime(n) == result


@pytest.mark.parametrize(
    "n, confidence, result",
    [
        (4_294_967_311, 0.999_999, True),
        (4_294_967_309, 0.999_999, False),
    ],
)
def test_mr_primality(n, confidence, result):
    assert mr_primality(n, confidence) == result


@pytest.mark.parametrize(
    "n, confidence, result",
    [
        (4_294_967_311, 1.0, True),
        (4_294_967_309, 1.0, False),
    ],
)
def test_aks_primality(n, confidence, result):
    _ = confidence  # type: ignore
    assert aks_primality(n) == result


def test_best_satisfiable():
    pass


@pytest.mark.parametrize(
    "n, confidence, result",
    [
        (64_489, None, True),
        (64_487, None, False),
        (262_147, None, True),
        (262_143, None, False),
        (4_294_967_311, 0.999_999_999, True),
        (4_294_967_309, 0.999_999_999, False),
        (4_294_967_311, None, True),  # Default MR confidence
        (4_294_967_309, None, False),  # Default MR confidence
        (4_294_967_311, 1.0, True),
        (4_294_967_309, 1.0, False),
    ],
)
def test_is_prime(n, confidence, result):
    if confidence is None:
        assert nums.is_prime(n) == result
    else:
        assert nums.is_prime(n, confidence) == result
