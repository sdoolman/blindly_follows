import itertools
import random

import numpy as np
import primefac


def xgcd(a, b):
    """return (g, x, y) such that a*x + b*y = g = gcd(a, b)"""
    x0, x1, y0, y1 = 0, 1, 1, 0
    while a != 0:  # TODO: use numpy's functionality
        q, b, a = b // a, a, b % a
        y0, y1 = y1, y0 - (q * y1)
        x0, x1 = x1, x0 - (q * x1)
    return b, x0, y0


def mulinv(a, b):
    """return x such that (x * a) % b == 1"""
    g, x, _ = xgcd(a, b)
    if g == 1:
        return x % b


def lagrange(x, w, ff):
    M = len(x)
    p = np.mod(np.poly1d(0.0), ff)
    for j in range(M):
        pt = np.mod(np.poly1d(w[j]), ff)
        for k in range(M):
            if k == j:
                continue
            fac_inv = mulinv(np.mod(x[j] - x[k], ff), ff)
            tmp = np.mod(np.mod(np.poly1d([1.0, -x[k]]), ff) * fac_inv, ff)
            pt = np.mod(pt * tmp, ff)
        p = np.mod(p + pt, ff)
    return p


def generate_primes(limit):
    return (p for p in set(x for x in range(2, limit) if not [t for t in range(2, x) if not x % t]))


def get_ab_primes(m0, limit, n, k):
    from sys import stdout
    assert k <= n
    primes = set(generate_primes(limit))
    # random.shuffle(m0)  # this could speed up the process
    for i, candidates in enumerate(sorted(itertools.combinations(primes, n))):  # consider using random sample
        stdout.write(f'{i}\r')  # indicate iteration number
        ms = [p * c for p, c in zip(m0, candidates)]
        if m0.value < min(ms) and ms == sorted(ms) and \
                m0.value * np.prod(ms[-k + 1:]) < np.prod(ms[:k], dtype=np.int64):  # sequence is ab increasing
            return ms

    raise RuntimeError('failed to get ab_primes!')


def get_ab_share(secret, primes):
    m0 = primes[0]
    q_param = (np.prod(primes[1:], dtype=np.int64) - secret) // m0
    alpha_param = random.randint(1, q_param)
    result = secret + alpha_param * m0
    assert result < np.prod(primes[1:], dtype=np.int64)
    return result


def get_primes(xy_s):
    xs = [x for x, _ in xy_s]
    diffs = set([abs(x1 - x2) for x1 in xs for x2 in xs if x1 != x2])
    factors = [list(r) for r in map(primefac.primefac, diffs)]
    primes_to_skip = set([p for subset in factors for p in subset])
    primes = get_ab_primes(range(100, 200), n=4, k=3,
                           to_skip=primes_to_skip)  # TODO: choose n,k in another way
    return primes
