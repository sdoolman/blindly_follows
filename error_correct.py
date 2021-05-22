import random

import numpy as np

from crr.mathlib import garner_algorithm


def damage_r(r):
    for i in range(len(r)):
        if r[i] != 0:
            r[i] = 0
            break


def recover(N: int, E: int, F: int, r: int) -> tuple:
    for y in range(1, E + 1):
        for z in range(0, F + 1):
            if (y * r) % N == z % N:
                print(f'y={y}, z={z}')
                return y, z
    raise ValueError


def main():
    pk = [2, 3, 5]
    k = int(np.prod(pk))
    pn = pk + [7, 11, 13]
    n = int(np.prod(pn))
    e = pn[-1]
    x = random.randint(int(np.sqrt(k)) + 1, k) ** 2
    print(f'x={x}, k={k}, n={n}, e={e}')
    r = [x % p for p in pn]
    print(f'r={r}')
    damage_r(r)
    print(f'r={r}')
    rerr = garner_algorithm(r, pn)
    try:
        y, z = recover(n, e, (k - 1) * e, rerr)
        x = z // y

    except ValueError:
        print('failed to recover!')
    print(f'x={x}')


if __name__ == '__main__':
    main()
