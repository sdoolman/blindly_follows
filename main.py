import numpy as np


class CRR(object):
    def __init__(self, *mods):
        self._mods = mods
        basis = []
        product = np.prod(self._mods)
        for m in mods:
            q = product // m
            r = np.mod(q, m)
            i = CRR.mulinv(r, m)
            basis += [q * i]
        self._basis = tuple(basis)

    @staticmethod
    def xgcd(a, b):
        """return (g, x, y) such that a*x + b*y = g = gcd(a, b)"""
        x0, x1, y0, y1 = 0, 1, 1, 0
        while a != 0:  # TODO: use numpy's functionality
            q, b, a = b // a, a, b % a
            y0, y1 = y1, y0 - q * y1
            x0, x1 = x1, x0 - q * x1
        return b, x0, y0

    @staticmethod
    def mulinv(a, b):
        """return x such that (x * a) % b == 1"""
        g, x, _ = CRR.xgcd(a, b)
        if g == 1:
            return x % b


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    # parser.add_argument('polynomial')
    args = parser.parse_args()

    a = np.array([1, 0, 1], dtype="uint8")
    b = np.array([1, 1], dtype="uint8")

    crr = CRR(8, 7, 5)
