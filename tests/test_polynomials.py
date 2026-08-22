"""Unit tests for modular arithmetic and polynomial operations over Z_M."""

from pathlib import Path

import pytest

from polynomials.polymod import Mod, PolyMod


class TestModArithmetic:
    def test_basic_arithmetic(self):
        Mod.set_mod(17)
        a = Mod(10)
        b = Mod(12)
        assert (a + b).value == (10 + 12) % 17
        assert (a - b).value == (10 - 12) % 17
        assert (a * b).value == (10 * 12) % 17
        assert (-a).value == (-10) % 17

    def test_negative_and_zero_inputs(self):
        Mod.set_mod(19)
        assert Mod(0).value == 0
        assert Mod(-1).value == 18
        assert Mod(-19).value == 0
        assert Mod(-20).value == 18

    def test_powers_and_stress_exponents(self):
        Mod.set_mod(23)
        a = Mod(5)
        assert a**0 == 1
        assert a**1 == 5
        assert a**2 == 2
        # Large stress exponent using Fermat's Little Theorem: a^(p-1) = 1 mod p (p=23, p-1=22)
        assert (a**22).value == 1
        assert (a**220002).value == (a**2).value

    def test_modular_inverse(self):
        Mod.set_mod(17)
        for x in range(1, 17):
            inv = Mod(x).inverse()
            assert (Mod(x) * inv).value == 1

    def test_non_coprime_inverse_raises(self):
        Mod.set_mod(12)
        # 4 and 12 share gcd 4 != 1
        with pytest.raises(ValueError, match="not co-prime"):
            Mod(4).inverse()
        with pytest.raises(ZeroDivisionError):
            Mod(0).inverse()

    def test_invalid_modulus(self):
        with pytest.raises(ValueError, match="positive integer"):
            Mod.set_mod(0)
        with pytest.raises(ValueError, match="positive integer"):
            Mod.set_mod(-5)


class TestPolyMod:
    def test_polymod_operations(self):
        Mod.set_mod(17)
        p1 = PolyMod([1, 2, 3])  # 1 + 2x + 3x^2
        p2 = PolyMod([4, 5])  # 4 + 5x
        assert (p1 + p2).terms == [Mod(5), Mod(7), Mod(3)]
        assert (p1 - p2).terms == [Mod(14), Mod(14), Mod(3)]

    def test_polymod_multiplication(self):
        Mod.set_mod(17)
        p1 = PolyMod([1, 1])  # 1 + x
        p2 = PolyMod([1, 1])  # 1 + x
        p_sq = p1 * p2  # 1 + 2x + x^2
        assert p_sq.terms == [Mod(1), Mod(2), Mod(1)]

    def test_zero_and_constant_polynomials(self):
        Mod.set_mod(17)
        p_zero = PolyMod([0, 0, 0])
        assert p_zero.zero()
        assert p_zero.degree == 0
        assert p_zero(10).value == 0

        p_const = PolyMod([7])
        assert p_const.degree == 0
        assert p_const(0).value == 7
        assert p_const(100).value == 7

    def test_poly_interpolation_edge_cases(self):
        Mod.set_mod(101)
        # Single point (degree 0)
        p1 = PolyMod.interpolate([(5, 42)])
        assert p1(5).value == 42
        assert p1(0).value == 42

        # 5 points interpolation
        points = [(1, 2), (2, 8), (3, 18), (4, 32), (5, 50)]  # y = 2x^2
        p2 = PolyMod.interpolate(points)
        for x, y in points:
            assert p2(x).value == y % 101
        assert p2(6).value == (2 * 36) % 101

    def test_json_serialization(self, tmp_path: Path):
        Mod.set_mod(97)
        poly = PolyMod([3, 14, 15, 92])
        json_file = tmp_path / "poly_test.json"
        poly.save_json(json_file)

        loaded = PolyMod.load_json(json_file)
        assert loaded == poly
        assert loaded(7).value == poly(7).value
