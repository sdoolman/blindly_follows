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


def generate_primes(limit, start_from=2):
    return (p for p in
            set(x for x in range(start_from, limit) if
                not x % 2 == 0 and not [t for t in range(3, int(round(np.sqrt(x))) + 1, 2) if not x % t]))


def get_ab_sequence(m0, limit, n, k):
    from sys import stdout
    assert k <= n and k <= len(m0) <= n
    primes = generate_primes(limit, start_from=m0.value // min(m0))
    # random.shuffle(m0)  # maybe improvement?
    for i, candidates in enumerate((itertools.combinations(primes, n))):  # random sampling could be quicker
        stdout.write(f'{i:,}\r')  # indicate iteration number
        ms = [p * c for p, c in zip(m0, candidates)]
        if m0.value < min(ms) and ms == sorted(ms) and \
                m0.value * np.prod(ms[-k + 1:], dtype=np.int64) < np.prod(ms[:k], dtype=np.int64):  # is ab increasing
            return ms

    raise Exception('failed to get ab_primes - consider a higher limit')


def get_ab_share(secret, m0, co_primes):
    q_param = (np.prod(co_primes, dtype=np.int64) - secret) // m0
    alpha_param = random.randint(1, q_param)
    result = secret + alpha_param * m0
    assert result < np.prod(co_primes, dtype=np.int64)
    return result


class M0(list):
    def __init__(self, *primes):
        super(M0, self).__init__(primes)

    @property
    def value(self):
        return int(np.prod(self, dtype=np.int64))


def get_ab_params(xy_s):
    xs = xy_s.keys()
    diffs = set([abs(x1 - x2) for x1 in xs for x2 in xs if x1 != x2])
    factors = set(itertools.chain.from_iterable([primefac.primefac(d) for d in diffs]))
    n, k = 4, 3
    m0 = M0(*itertools.islice((p for p in generate_primes(300) if p not in factors), k))
    ms = get_ab_sequence(m0, limit=100 * 1000, n=n, k=k)  # TODO: choose n,k in another way
    return m0.value, ms
