"""Unit tests, stress inputs, and edge cases for secret sharing and primality testing."""

import pytest

from polynomials.shamir import make_random_shares, recover_secret
from secret_sharing.bloom import AsmuthBloom
from secret_sharing.mathlib import (
    bit_len,
    get_consecutive_primes,
    get_prime,
    get_sg_prime,
    miller_rabin_test,
    primality_test,
    primality_test_for_sg_prime,
)


class TestPrimalityTests:
    def test_bit_length(self):
        assert bit_len(0) == 0
        assert bit_len(1) == 1
        assert bit_len(2) == 2
        assert bit_len(255) == 8
        assert bit_len(256) == 9

    def test_known_primes(self):
        # Known Mersenne primes: 2^13 - 1, 2^17 - 1, 2^19 - 1
        for p in (8191, 131071, 524287):
            assert primality_test(p)

    def test_carmichael_numbers(self):
        # Carmichael numbers fool Fermat primality tests, but Miller-Rabin detects them as composite
        carmichael_numbers = [561, 1105, 1729, 2465, 2821]
        for num in carmichael_numbers:
            assert not miller_rabin_test(num, rounds=20)
            assert not primality_test(num)

    def test_prime_generators(self):
        p = get_prime(16)
        assert primality_test(p)
        assert bit_len(p) == 16

        sg = get_sg_prime(16)
        assert primality_test_for_sg_prime(sg)
        assert primality_test(2 * sg + 1)

        consec = list(get_consecutive_primes(3, 16))
        assert len(consec) == 3
        for c in consec:
            assert primality_test(c)


class TestShamirSecretSharing:
    def test_shamir_threshold_and_subsets(self):
        secret, shares = make_random_shares(minimum=3, shares=6)
        # Any 3 shares out of 6 must reconstruct the exact secret
        assert recover_secret([shares[0], shares[1], shares[2]]) == secret
        assert recover_secret([shares[1], shares[3], shares[5]]) == secret
        assert recover_secret([shares[0], shares[4], shares[5]]) == secret

    def test_shamir_edge_cases(self):
        # Invalid minimum threshold > shares
        with pytest.raises(ValueError, match="cannot exceed"):
            make_random_shares(minimum=5, shares=3)

        # Reconstructing with < 2 shares raises error
        with pytest.raises(ValueError, match="at least two shares"):
            recover_secret([(1, 42)])


class TestAsmuthBloomScheme:
    def test_asmuth_bloom_threshold_reconstruction(self):
        threshold = (3, 5)
        ab = AsmuthBloom(threshold)
        test_secret = 987654321
        shares = ab.generate_shares(test_secret, k=64, h=128)
        assert len(shares) == 5

        # First 3 shares reconstruct correctly
        recovered = ab.combine_shares(shares[:3])
        assert recovered == test_secret

        # Any 3 shares reconstruct correctly
        recovered_alt = ab.combine_shares([shares[0], shares[2], shares[4]])
        assert recovered_alt == test_secret

    def test_asmuth_bloom_insufficient_shares_fail(self):
        threshold = (3, 5)
        ab = AsmuthBloom(threshold)
        test_secret = 123456
        shares = ab.generate_shares(test_secret, k=64, h=128)
        # Recombining with only 2 shares (k-1) should NOT match secret
        insufficient_recovered = ab.combine_shares(shares[:2])
        assert insufficient_recovered != test_secret
