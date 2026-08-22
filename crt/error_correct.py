"""Error correction for Chinese Remainder Theorem."""

import random

import numpy as np

from secret_sharing.mathlib import garner_algorithm


def damage_r(r: list[int]) -> None:
    """Inject a random single-element error into the share array."""
    if not r:
        return
    i = random.randrange(len(r))
    r[i] += 1


def recover(n_mod: int, e_param: int, f_param: int, r_val: int) -> tuple[int, int]:
    """Recover original value from erroneous CRT representation."""
    for y in range(1, e_param + 1):
        for z in range(0, f_param + 1):
            if (y * r_val) % n_mod == z % n_mod:
                return y, z
    raise RuntimeError("Recovery failed - could not find valid (y, z)")


def main() -> None:
    pk = [2, 3, 5]
    k = int(np.prod(pk))
    pn = pk + [7, 11, 13]
    n = int(np.prod(pn))
    e = pn[-1]
    x = random.randint(int(np.sqrt(k)) + 1, k) ** 2
    print(f"x={x}, k={k}, n={n}, e={e}")
    r = [x % p for p in pn]
    print(f"r={r}")
    damage_r(r)
    print(f"erroneous={r}")
    rerr = garner_algorithm(r, pn)
    try:
        y, z = recover(n, e, (k - 1) * e, rerr)
        recovered_x = z // y
        print(f"recovered x={recovered_x}")
    except RuntimeError as err:
        print(f"recovery failed: {err}")


if __name__ == "__main__":
    main()
