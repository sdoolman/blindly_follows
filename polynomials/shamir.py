"""Shamir's Secret Sharing Scheme over finite fields."""

import functools
import random
from collections.abc import Sequence

# 12th Mersenne Prime (2^127 - 1)
_PRIME: int = 2**127 - 1
_RINT = functools.partial(random.SystemRandom().randint, 0)


def eval_at(poly: Sequence[int], x: int, prime: int) -> int:
    """Evaluate polynomial at point x modulo prime using Horner's method."""
    accum = 0
    for coeff in reversed(poly):
        accum = (accum * x + coeff) % prime
    return accum


def make_random_shares(
    minimum: int, shares: int, prime: int = _PRIME
) -> tuple[int, list[tuple[int, int]]]:
    """Generate a random Shamir secret pool with threshold (minimum) and share points."""
    if minimum > shares:
        raise ValueError("Minimum threshold cannot exceed total number of shares")
    poly = [_RINT(prime) for _ in range(minimum)]
    points = [(i, eval_at(poly, i, prime)) for i in range(1, shares + 1)]
    return poly[0], points


def extended_gcd(a: int, b: int) -> tuple[int, int]:
    """Extended Euclidean algorithm computing multiplicative inverse modulo p."""
    x, last_x = 0, 1
    y, last_y = 1, 0
    while b != 0:
        quot = a // b
        a, b = b, a % b
        x, last_x = last_x - quot * x, x
        y, last_y = last_y - quot * y, y
    return last_x, last_y


def divmod_mod(num: int, den: int, p: int) -> int:
    """Compute (num / den) modulo prime p using explicit Extended Euclidean inverse."""
    inv, _ = extended_gcd(den, p)
    return (num * inv) % p


def lagrange_interpolate(x: int, x_s: Sequence[int], y_s: Sequence[int], p: int) -> int:
    """Find the y-value for x given points (x_s, y_s) over finite field mod p."""
    k = len(x_s)
    if k != len(set(x_s)):
        raise ValueError("Share x-coordinates must be distinct")

    total = 0
    for i in range(k):
        xi, yi = x_s[i], y_s[i]
        num, den = 1, 1
        for j in range(k):
            if i != j:
                xj = x_s[j]
                num = (num * (x - xj)) % p
                den = (den * (xi - xj)) % p
        total = (total + yi * divmod_mod(num, den, p)) % p
    return total % p


def recover_secret(shares: Sequence[tuple[int, int]], prime: int = _PRIME) -> int:
    """Recover secret from share points (x, y)."""
    if len(shares) < 2:
        raise ValueError("Need at least two shares to reconstruct")
    x_s = [s[0] for s in shares]
    y_s = [s[1] for s in shares]
    return lagrange_interpolate(0, x_s, y_s, prime)


def main() -> None:
    secret, shares = make_random_shares(minimum=3, shares=6)
    print(f"Secret: {secret}")
    print("Shares:")
    for share in shares:
        print(f"  {share}")

    print(f"Recovered (subset 0..3): {recover_secret(shares[:3])}")
    print(f"Recovered (subset 3..6): {recover_secret(shares[-3:])}")


if __name__ == "__main__":
    main()
