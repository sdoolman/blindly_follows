import hashlib
import random

import numpy as np

from crr.generic_functions import get_ab_share
from crr.polymod import Mod, PolyMod


def main():
    m0 = 11 * 13 * 17
    ms = [17 * 223, 13 * 227, 11 * 229]
    freq = {
        m: np.zeros(m) for m in ms
    }
    expected = hashlib.sha256()
    actual = hashlib.sha256()
    for _ in range(10 ** 6):
        i = random.randint(1, 10)
        expected.update(chr(i).encode())
        share = get_ab_share(i, m0, ms)
        shares = list()
        for m in ms:
            Mod.set_mod(m)
            v = PolyMod([2, 3])(share).value
            shares += [v]
            freq[m][v] += 1
        from crr.mathlib import garner_algorithm
        Mod.set_mod(m0)
        v = ((Mod(garner_algorithm(shares, ms)) - 2) * Mod(3).inverse()).value
        actual.update(chr(v).encode())
    from matplotlib import pyplot as plt
    for m in freq:
        max_freq = np.max(freq[m])
        fig, (ax1, ax2) = plt.subplots(2)
        fig.suptitle(f'mod={m}')
        ax1.plot(np.arange(m), freq[m], 'b.', markersize=1)
        ax1.set_yticks(np.arange(0, max_freq + 1, 100))
        ax2.hist(freq[m])
        ax2.set_yscale("log")
        ax2.set_xticks(np.arange(0, max_freq + 1, 100))
        plt.savefig(f'{m}.png')
        plt.close()

    print(f'expected=[{expected.hexdigest()}]\n  actual=[{actual.hexdigest()}]')
