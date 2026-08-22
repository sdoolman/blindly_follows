"""Generic functions for Chinese Remainder Theorem (CRT) and Mignotte threshold schemes."""

import itertools
import math
import random
import sys
from collections.abc import Iterable, Sequence

import numpy as np
import primefac


def xgcd(a: int, b: int) -> tuple[int, int, int]:
    """Return (g, x, y) such that a*x + b*y = g = gcd(a, b)."""
    x0, x1, y0, y1 = 0, 1, 1, 0
    while a != 0:
        q, b, a = b // a, a, b % a
        y0, y1 = y1, y0 - (q * y1)
        x0, x1 = x1, x0 - (q * x1)
    return b, x0, y0


def mulinv(a: int, b: int) -> int | None:
    """Return modular multiplicative inverse x such that (x * a) % b == 1."""
    g, x, _ = xgcd(a, b)
    if g == 1:
        return x % b
    return None


def lagrange(x: Sequence[float | int], w: Sequence[float | int], ff: int) -> np.poly1d:
    """Compute modular Lagrange polynomial over finite field mod ff."""
    num_points = len(x)
    poly = np.mod(np.poly1d(0.0), ff)
    for j in range(num_points):
        poly_term = np.mod(np.poly1d(w[j]), ff)
        for k in range(num_points):
            if k == j:
                continue
            fac_inv = mulinv(int(np.mod(x[j] - x[k], ff)), ff)
            if fac_inv is None:
                raise ValueError(f"No modular inverse for {x[j] - x[k]} mod {ff}")
            tmp = np.mod(np.mod(np.poly1d([1.0, -x[k]]), ff) * fac_inv, ff)
            poly_term = np.mod(poly_term * tmp, ff)
        poly = np.mod(poly + poly_term, ff)
    return poly


def generate_primes(limit: int, start_from: int = 2) -> list[int]:
    """Generate prime numbers in range [start_from, limit)."""
    if limit <= 2:
        return []
    sieve = [True] * limit
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit, i):
                sieve[j] = False
    return [p for p in range(max(2, start_from), limit) if sieve[p]]


def get_authorized_range(primes: Iterable[int], n: int, k: int) -> tuple[range, list[int]]:
    """Find an authorized sequence of n coprime moduli with threshold k for Mignotte scheme."""
    assert k <= n, "Threshold k must be <= n"
    for i, candidates in enumerate(itertools.combinations(primes, n)):
        sys.stdout.write(f"{i:,}\r")
        ms = sorted(candidates)
        beta = math.prod(ms[-k + 1 :])
        alpha = math.prod(ms[:k])
        if beta < alpha:
            return range(beta + 1, alpha), ms

    raise RuntimeError("Failed to find primes - consider a higher search limit")


def get_ab_share(secret: int, m0: int, co_primes: Sequence[int]) -> int:
    """Compute Asmuth-Bloom share."""
    prod = math.prod(co_primes)
    q_param = (prod - secret) // m0
    alpha_param = random.randint(1, max(1, q_param))
    return secret + alpha_param * m0


def get_mignotte_params(
    xy_s: dict[int, int] | Sequence[tuple[int, int]], n: int = 3, k: int = 3
) -> tuple[range, list[int]]:
    """Compute Mignotte coprime parameters for input domain xy_s."""
    if isinstance(xy_s, dict):
        xs = list(xy_s.keys())
    else:
        xs = [x for x, _ in xy_s]

    diffs = {abs(x1 - x2) for x1 in xs for x2 in xs if x1 != x2}
    factors = set(itertools.chain.from_iterable(primefac.primefac(d) for d in diffs if d > 0))

    available_primes = [p for p in generate_primes(1000, start_from=200) if p not in factors]
    return get_authorized_range(available_primes, n, k)
