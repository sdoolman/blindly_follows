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


def get_authorized_range(primes, n, k):
    from sys import stdout
    assert k <= n
    for i, candidates in enumerate((itertools.combinations(primes, n))):  # 'choose' behavior
        stdout.write(f'{i:,}\r')  # iteration number
        ms = sorted(candidates)
        beta = int(np.prod(ms[-k + 1:]))
        alpha = int(np.prod(ms[:k], dtype=np.int64))
        if beta < alpha:
            return range(beta + 1, alpha), ms  # array is authorized

    raise Exception('failed to get ab_primes - consider a higher limit')


def get_ab_share(secret, m0, co_primes):
    prod = np.prod(co_primes, dtype=np.int64)
    q_param = (prod - secret) // m0
    alpha_param = random.randint(1, q_param)
    result1 = secret + alpha_param * m0

    # offset = random.randint(1, prod - result1 - 1)
    # q_param = (prod - offset) // m0
    # alpha_param = random.randint(1, q_param)
    # result2 = offset + alpha_param * m0
    #
    # assert result2 < prod and result1 + offset < prod

    # return result2, result1 + offset

    return result1


def get_mignotte_params(xy_s, n=3, k=3):
    xs = xy_s.keys()
    diffs = set([abs(x1 - x2) for x1 in xs for x2 in xs if x1 != x2])
    factors = set(itertools.chain.from_iterable([primefac.primefac(d) for d in diffs]))

    return get_authorized_range(itertools.islice((p for p in generate_primes(300) if p not in factors), k), n, k)
