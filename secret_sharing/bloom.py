#!/usr/bin/env python3
"""Asmuth-Bloom threshold secret sharing scheme implementation."""

import argparse
import binascii
import random
import sys
from collections.abc import Sequence
from pathlib import Path

from secret_sharing import mathlib


class AsmuthBloom:
    """Asmuth-Bloom Threshold Secret Sharing Scheme."""

    def __init__(self, threshold: tuple[int, int]) -> None:
        # threshold is (shares needed to recombine, all shares total)
        self.threshold: tuple[int, int] = threshold
        self.shares: list[tuple[int, int]] | None = None
        self._m_0: int = 0
        self._y: int = 0

    def _find_group_for_secret(self, k: int) -> int:
        while True:
            m_0 = mathlib.get_prime(k)
            if mathlib.primality_test(m_0):
                return m_0

    def _check_base_condition(self, d: Sequence[int]) -> bool:
        recomb_count, all_count = self.threshold
        left = 1
        for i in range(1, recomb_count + 1):
            left *= d[i]

        right = d[0]
        for i in range(recomb_count - 1):
            right *= d[all_count - i]
        return left > right

    def _get_pairwise_primes(self, k: int, h: int) -> list[int]:
        if h < k:
            raise ValueError("Not enough bits for m_1 (h must be >= k)")
        _, all_count = self.threshold
        p = self._find_group_for_secret(k)
        while True:
            d = [p]
            for prime in mathlib.get_consecutive_primes(all_count, h):
                d.append(prime)
            if self._check_base_condition(d):
                return d

    def _prod(self, coprimes: Sequence[int]) -> int:
        total = 1
        t, _ = self.threshold
        for i in range(t):
            total *= coprimes[i]
        return total

    def _get_modulo_base(self, secret: int, coprimes: Sequence[int]) -> int:
        prod = self._prod(coprimes)
        while True:
            a_param = mathlib.get_random_range(1, (prod - secret) // self._m_0)
            y = secret + a_param * self._m_0
            if 0 <= y < prod:
                return y

    def generate_shares(self, secret: int, k: int, h: int) -> list[tuple[int, int]]:
        """Generate (share, mod) pairs for secret using (k, h) bit parameters."""
        if mathlib.bit_len(secret) > k:
            raise ValueError("Secret exceeds bit length k")

        m = self._get_pairwise_primes(k, h)
        self._m_0 = m.pop(0)
        self._y = self._get_modulo_base(secret, m)

        self.shares = [(self._y % m_i, m_i) for m_i in m]
        return self.shares

    def combine_shares(self, shares: Sequence[tuple[int, int]]) -> int:
        """Recombine subset of shares to recover original secret."""
        y_i = [x for x, _ in shares]
        m_i = [x for _, x in shares]
        y = mathlib.garner_algorithm(y_i, m_i)
        return y % self._m_0


def string_to_int(s: bytes | str) -> int:
    """Convert string/bytes into large integer."""
    raw = s.encode("utf-8") if isinstance(s, str) else s
    return int(binascii.hexlify(raw), 16)


def main() -> None:
    parser = argparse.ArgumentParser(description="Asmuth-Bloom Threshold Secret Sharing")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--random",
        type=int,
        metavar="BITS",
        help="Generate random secret with given bit length",
    )
    group.add_argument("--file", type=Path, metavar="PATH", help="Read secret from file")
    group.add_argument("--text", type=str, metavar="STRING", help="Use text string as secret")
    parser.add_argument("M", type=int, help="Total number of shares")
    parser.add_argument("N", type=int, help="Threshold number of shares needed for recovery")

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    if args.N > args.M:
        print("Error: Threshold N cannot exceed total shares M")
        sys.exit(1)

    if args.random:
        secret = random.SystemRandom().getrandbits(args.random)
    elif args.file:
        secret = string_to_int(args.file.read_bytes())
    else:
        secret = string_to_int(args.text)

    threshold = (args.N, args.M)
    m_0_bits = 500
    m_1_bits = 800

    print("--------------------------------------")
    print(f"Secret: {secret}")

    ab = AsmuthBloom(threshold)
    try:
        shares = ab.generate_shares(secret, m_0_bits, m_1_bits)
    except ValueError as e:
        print(f"Cannot generate shares: {e}")
        sys.exit(1)

    print("Secret shares:")
    for i, share in enumerate(shares):
        print(f"{i + 1}: {share}")

    print("--------------------------------------")
    print("Checking result with first N shares:")
    recovered = ab.combine_shares(shares[: args.N])
    print(f"Recombined secret: {recovered}")
    print(f"Status: {'SUCCESS' if recovered == secret else 'FAILED'}")
    print("--------------------------------------")


if __name__ == "__main__":
    main()
