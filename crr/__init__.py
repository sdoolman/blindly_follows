import numpy as np

###################################################################################################
from crr.generic_functions import mulinv


class CRR(object):
    def __init__(self, *moduli):
        self._product = np.prod(moduli, dtype="uint16")
        self._moduli = moduli
        self._basis_vector = tuple(CRR.calc_basis(self._moduli, self._product))

    @staticmethod
    def calc_basis(moduli, product):
        basis_vector = []
        for m in moduli:
            q = product // m
            r = np.mod(q, m)
            i = mulinv(r, m)
            basis_vector += [q * i]
        return basis_vector

    def _apply(self, a, b, f):
        res_vec = np.mod(f(a, b), self._moduli)
        res_sum = np.sum(np.multiply(res_vec, self._basis_vector))
        return np.mod(res_sum, self._product)

    def add(self, a, b):
        return self._apply(a, b, np.add)

    def mul(self, a, b):
        return self._apply(a, b, np.multiply)
