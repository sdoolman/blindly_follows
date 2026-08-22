"""Asmuth-Bloom shares arithmetic and frequency analysis simulation."""

import hashlib
import random
import string

import numpy as np
from matplotlib import pyplot as plt
from progressbar import progressbar

from crt.generic_functions import get_ab_share
from polynomials.polymod import Mod, PolyMod
from secret_sharing.mathlib import garner_algorithm

NUMBER_OF_ITERATIONS: int = 10**4


def run_arithmetic_simulation(iterations: int = NUMBER_OF_ITERATIONS) -> None:
    """Run Asmuth-Bloom threshold sharing arithmetic simulation."""
    m0 = 11 * 13 * 17
    ms = [17 * 223, 13 * 227, 11 * 229]

    freq = {m: np.zeros(m, dtype=int) for m in ms}

    expected = hashlib.sha256()
    actual = hashlib.sha256()

    for _ in progressbar(range(iterations)):
        s = random.choice(string.ascii_lowercase)
        share = get_ab_share(ord(s), m0, ms)
        shares = []
        for m in ms:
            Mod.set_mod(m)
            v = PolyMod([2, 4])(share).value
            shares.append(v)
            freq[m][v] += 1

        Mod.set_mod(m0)
        r = garner_algorithm(shares, ms)
        r = int(PolyMod([-2, 0.25])(r).value)

        expected.update(s.encode())
        actual.update(chr(r).encode())

    print(f"expected=[{expected.hexdigest()}]\n actual=[{actual.hexdigest()}]")

    for m in freq:
        fig, (ax1, ax2) = plt.subplots(2)
        fig.suptitle(f"mod={m}")
        ax1.plot(np.arange(m), freq[m], "b.", markersize=1)
        ax2.hist(freq[m])
        ax2.set_yscale("log")
    plt.show()
    plt.close()


def main() -> None:
    run_arithmetic_simulation()


if __name__ == "__main__":
    main()
