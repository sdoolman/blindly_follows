import itertools

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


def get_ab_primes(threshold, n, k, to_skip=None):
    if to_skip is None:
        to_skip = set()
    assert k < n
    generated = [x for x in range(2, threshold) if not [t for t in range(2, x) if not x % t]]
    primes = set(generated).difference(to_skip)
    m_0 = min(primes)
    for comb in itertools.combinations(primes - {m_0}, n):
        for m in itertools.permutations(comb):
            if m_0 * np.prod(m[-k + 1:]) < np.prod(m[:k], dtype=np.int64):
                return [m_0] + list(m)

    raise RuntimeError('failed to get ab_primes!')


def get_primes(xy_s):
    xs = [x for x, _ in xy_s]
    diffs = set([abs(x1 - x2) for x1 in xs for x2 in xs if x1 != x2])
    factors = [list(r) for r in map(primefac.primefac, diffs)]
    primes_to_skip = set([p for subset in factors for p in subset])
    primes = get_ab_primes(max(primes_to_skip), n=4, k=3, to_skip=primes_to_skip)  # TODO: choose n,k in another way
    return primes
