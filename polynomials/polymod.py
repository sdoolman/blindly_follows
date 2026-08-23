"""Modular arithmetic and polynomial operations over finite fields and modular rings.

Implements explicit algebraic algorithms (Extended Euclidean GCD, square-and-multiply,
and Lagrange interpolation) faithful to the underlying cryptographic theory.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path


class Mod:
    """Represents an element in the modular ring Z_M with explicit algebraic operations."""

    M: int = 17

    @staticmethod
    def set_mod(n: int) -> None:
        """Set the global ring modulus M."""
        if n > 0 and isinstance(n, int):
            Mod.M = n
        else:
            raise ValueError("Modulus must be a positive integer.")

    @staticmethod
    def math_mod(a: int) -> int:
        """Explicit mathematical modulo reduction guaranteeing positive residue in [0, M-1]."""
        return ((a % Mod.M) + Mod.M) % Mod.M

    @staticmethod
    def exp_mod(a: int, k: int) -> int:
        """Explicit square-and-multiply modular exponentiation: a^k mod M."""
        if k == 0:
            return 1
        if k == 1:
            return Mod.math_mod(a)
        if k % 2 == 0:
            z = Mod.exp_mod(a, k // 2)
            return Mod.math_mod(z * z)
        z = Mod.exp_mod(a, (k - 1) // 2)
        return Mod.math_mod(a * z * z)

    @staticmethod
    def egcd(a: int, b: int) -> tuple[int, int, int]:
        """Extended Euclidean Algorithm returning (gcd, x, y) such that a*x + b*y = gcd(a, b)."""
        if b == 0:
            return a, 1, 0
        d, x, y = Mod.egcd(b, a % b)
        return d, y, x - (a // b) * y

    def __init__(self, n: int | Mod) -> None:
        if isinstance(n, Mod):
            self.value: int = n.value
        else:
            self.value: int = Mod.math_mod(n)

    def __neg__(self) -> Mod:
        return Mod(-self.value)

    def __add__(self, m: int | Mod) -> Mod:
        val = m.value if isinstance(m, Mod) else m
        return Mod(self.value + val)

    def __sub__(self, m: int | Mod) -> Mod:
        val = m.value if isinstance(m, Mod) else m
        return Mod(self.value - val)

    def __mul__(self, m: int | Mod) -> Mod:
        val = m.value if isinstance(m, Mod) else m
        return Mod(self.value * val)

    def __radd__(self, other: int | Mod) -> Mod:
        return self if other == 0 else self.__add__(other)

    def __rsub__(self, other: int | Mod) -> Mod:
        return Mod(other - self.value)

    def __rmul__(self, other: int | Mod) -> Mod:
        return self.__mul__(other)

    def __iadd__(self, m: int | Mod) -> Mod:
        val = m.value if isinstance(m, Mod) else m
        self.value = Mod.math_mod(self.value + val)
        return self

    def __isub__(self, m: int | Mod) -> Mod:
        val = m.value if isinstance(m, Mod) else m
        self.value = Mod.math_mod(self.value - val)
        return self

    def __imul__(self, m: int | Mod) -> Mod:
        val = m.value if isinstance(m, Mod) else m
        self.value = Mod.math_mod(self.value * val)
        return self

    def __pow__(self, k: int) -> Mod:
        return Mod(Mod.exp_mod(self.value, k))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Mod({self.value}, M={Mod.M})"

    def __eq__(self, m: object) -> bool:
        if isinstance(m, Mod):
            return self.value == m.value
        if isinstance(m, int):
            return self.value == Mod.math_mod(m)
        return False

    def __ne__(self, m: object) -> bool:
        return not self.__eq__(m)

    def inverse(self) -> Mod:
        """Compute modular multiplicative inverse via Extended Euclidean Algorithm."""
        if self.value == 0:
            raise ZeroDivisionError("Inverse of 0 is undefined.")
        val = Mod.egcd(Mod.M, self.value)
        if val[0] == 1:
            return Mod(val[2])
        raise ValueError(
            f"Mod ({Mod.M}) and value ({self.value}) are not co-prime (gcd={val[0]}). "
            "Inverse is undefined."
        )


class PolyMod:
    """Polynomial with coefficients in modular ring Z_M."""

    @staticmethod
    def interpolate(points: Sequence[tuple[int, int]]) -> PolyMod:
        """Construct polynomial passing through points using explicit Lagrange basis polynomials."""
        deltas = []
        s = PolyMod([0])
        n = len(points)
        for i in range(n):
            num = PolyMod([1])
            den = Mod(1)
            for j in range(n):
                if i != j:
                    num *= PolyMod([-points[j][0], 1])
                    den *= Mod(points[i][0] - points[j][0])
            deltas.append(num * den.inverse().value)
        for i in range(n):
            s += deltas[i] * Mod(points[i][1])
        return s

    def __init__(self, terms: Sequence[int | Mod]) -> None:
        if isinstance(terms, Sequence):
            self.terms: list[Mod] = [Mod(t) for t in terms]
        else:
            raise TypeError("Terms must be a sequence.")
        self.degree: int = 0
        for i in range(len(self.terms) - 1, -1, -1):
            if self.terms[i] != 0:
                self.degree = i
                break

    def get_terms(self) -> list[int]:
        return [t.value for t in self.terms]

    def __getitem__(self, item: int) -> Mod:
        return self.terms[item]

    def __setitem__(self, key: int, value: int | Mod) -> None:
        self.terms[key] = Mod(value)

    def __call__(self, x: int | Mod) -> Mod:
        out = Mod(0)
        x_val = Mod(x)
        for i, term in enumerate(self.terms):
            out += term * (x_val**i)
        return out

    def __len__(self) -> int:
        return len(self.terms)

    def __str__(self) -> str:
        out = ""
        i = self.degree
        while i >= 0:
            if i != self.degree and self.terms[i] != 0:
                out += "+"
            if i == 0 and self.terms[i] != 0:
                out += str(self.terms[i])
            elif self.terms[i] != 1 and self.terms[i] != 0:
                out += str(self.terms[i])
                out += f"x^{i}" if i != 1 else "x"
            elif self.terms[i] != 0:
                out += f"x^{i}" if i != 1 else "x"
            i -= 1
        return out if out else "0"

    def __add__(self, p: PolyMod) -> PolyMod:
        ply = []
        c = 0
        for i in range(max(len(self.terms), len(p))):
            if c >= len(self.terms):
                ply.insert(i, p[i])
            elif c >= len(p):
                ply.insert(i, self.terms[i])
            else:
                ply.insert(i, p[i] + self.terms[i])
            c += 1
        return PolyMod(ply)

    def __sub__(self, p: PolyMod) -> PolyMod:
        ply = []
        c = 0
        for i in range(max(len(self.terms), len(p))):
            if c >= len(self.terms):
                ply.insert(i, -p[i])
            elif c >= len(p):
                ply.insert(i, self.terms[i])
            else:
                ply.insert(i, self.terms[i] - p[i])
            c += 1
        return PolyMod(ply)

    def __mul__(self, p: PolyMod | int | Mod) -> PolyMod:
        ply: list[Mod] = []
        if isinstance(p, PolyMod):
            for i in range(len(self.terms)):
                for j in range(len(p)):
                    try:
                        ply[i + j] += self.terms[i] * p[j]
                    except (IndexError, TypeError):
                        ply.insert(i + j, self.terms[i] * p[j])
        else:
            for i in range(len(self.terms)):
                ply.insert(i, self.terms[i] * p)
        return PolyMod(ply)

    def __iadd__(self, p: PolyMod) -> PolyMod:
        return self + p

    def __isub__(self, p: PolyMod) -> PolyMod:
        return self - p

    def __imul__(self, p: PolyMod | int | Mod) -> PolyMod:
        if isinstance(p, PolyMod):
            return self * p
        for i in range(len(self.terms)):
            self.terms[i] *= p
        return self

    def __eq__(self, p: object) -> bool:
        if not isinstance(p, PolyMod):
            return False
        if len(self.terms) != len(p.terms):
            return False
        for i, term in enumerate(p.terms):
            if self.terms[i] != term:
                return False
        return True

    def __ne__(self, p: object) -> bool:
        return not (self == p)

    def zero(self) -> bool:
        return all(i == 0 for i in self.terms)

    def to_dict(self) -> dict:
        return {
            "modulus": Mod.M,
            "coefficients": [t.value for t in self.terms],
        }

    @classmethod
    def from_dict(cls, data: dict) -> PolyMod:
        Mod.set_mod(data.get("modulus", Mod.M))
        return cls([c for c in data.get("coefficients", [])])

    def save_json(self, filepath: Path | str) -> None:
        path = Path(filepath)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_json(cls, filepath: Path | str) -> PolyMod:
        path = Path(filepath)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)
