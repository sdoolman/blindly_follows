"""Unit tests and edge cases for CRT and Mignotte threshold schemes."""

import math
import random

import pytest

from crt.generic_functions import (
    generate_primes,
    get_mignotte_params,
    mulinv,
    xgcd,
)
from secret_sharing.mathlib import garner_algorithm


class TestCRTBasics:
    def test_xgcd_and_mulinv(self):
        # Coprime case
        g, x, y = xgcd(35, 15)
        assert g == 5
        assert 35 * x + 15 * y == 5

        # Modular inverse
        inv = mulinv(3, 11)
        assert (3 * inv) % 11 == 1

        # Non-coprime inverse
        assert mulinv(6, 9) is None

    def test_generate_primes_edge_cases(self):
        assert generate_primes(1) == []
        assert generate_primes(2) == []
        assert generate_primes(3) == [2]
        assert generate_primes(10) == [2, 3, 5, 7]
        assert generate_primes(20, start_from=10) == [11, 13, 17, 19]


class TestGarnerAlgorithm:
    @pytest.mark.parametrize(
        "secret",
        [
            0,
            1,
            42,
            1000,
            999999,
        ],
    )
    def test_garner_reconstruction_stress(self, secret: int):
        ms = [233, 239, 241, 251, 257]  # 5 coprime moduli
        prod = math.prod(ms)
        secret_mod = secret % prod
        shares = [secret_mod % m for m in ms]
        reconstructed = garner_algorithm(shares, ms)
        assert reconstructed == secret_mod

    def test_garner_maximum_boundary(self):
        ms = [101, 103, 107]
        max_secret = math.prod(ms) - 1
        shares = [max_secret % m for m in ms]
        assert garner_algorithm(shares, ms) == max_secret

    def test_mignotte_scheme_end_to_end(self):
        transitions = {100: 200, 200: 300, 300: 400}
        authorized_range, ms = get_mignotte_params(transitions, n=5, k=4)
        assert len(ms) == 5
        assert authorized_range.start < authorized_range.stop

        for _ in range(10):
            secret = random.choice(authorized_range)
            shares = [(secret % mi, mi) for mi in ms[:4]]
            reconstructed = garner_algorithm([x for x, _ in shares], [x for _, x in shares])
            assert reconstructed == secret
