import secrets


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


def IsPrime(n):
    k = min(int(len(str(n)) / 5) + 4, 14)
    if n <= 3:
        return n > 1
    if n & 1 == 0:
        return False
    d = n - 1
    while d % 2 == 0:
        d //= 2
    for _ in range(k):
        if millerTest(d, n) == False:
            return False
    return True
