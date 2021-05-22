import hashlib
import numpy as np
import random
import string
from matplotlib import pyplot as plt
from progressbar import progressbar

from crr.generic_functions import get_ab_share
from crr.polymod import Mod, PolyMod
from crr.mathlib import garner_algorithm

NUMBER_OF_ITERATIONS = 10**6


def main():
    m0 = 11 * 13 * 17
    ms = [17 * 223, 13 * 227, 11 * 229]  # coprime moduli

    freq = {m: np.zeros(m, dtype=int)
            for m in ms}  # count the different shares for each modulo

    expected = hashlib.sha256()
    actual = hashlib.sha256()

    for _ in progressbar(range(NUMBER_OF_ITERATIONS)):
        # generate random secret
        s = random.choice(string.ascii_lowercase)
        # find Asmuth-Bloom secret shares
        share = get_ab_share(ord(s), m0, ms)
        shares = list()
        for m in ms:
            Mod.set_mod(m)
            v = PolyMod([2, 4])(share).value  # p(x)=4x+2
            shares += [v]
            freq[m][v] += 1

        # restore secret from all shares
        Mod.set_mod(m0)
        r = garner_algorithm(shares, ms)
        r = int(PolyMod([-2, 0.25])(r).value)  # p(x)=0.25x-2

        expected.update(s.encode())
        actual.update(chr(r).encode())

        # TODO: this is true only when p(x)=x, we should solve this somehow...
        print(
            f'expected=[{expected.hexdigest()}]\n actual=[{actual.hexdigest()}]'
        )

    for m in freq:
        max_freq = np.max(freq[m])  # find the most frequent share
        fig, (ax1, ax2) = plt.subplots(2)
        fig.suptitle(f'mod={m}')

        ax1.plot(np.arange(m), freq[m], 'b.', markersize=1)

        ax2.hist(freq[m])
        ax2.set_yscale("log")
    plt.show()
    plt.close()


if __name__ == '__main__':
    main()
