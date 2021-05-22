import itertools
from sys import stdout

import numpy as np

from crr.mathlib import garner_algorithm
from crr.polymod import Mod


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('known_shares_files', nargs='+', metavar='MOD.dat')
    parser.add_argument('unknown_shares_file', metavar='MOD.dat')
    parser.add_argument('field_modulo', type=int)

    args = parser.parse_args()

    def extract_shares(shares_file):
        freq = np.memmap(shares_file, mode='r', dtype=np.int64)
        return np.where(freq != 0)[0], np.size(freq)

    known_shares_col, known_mods = zip(
        *[extract_shares(sf) for sf in args.known_shares_files])
    unknown_shares, unknown_mod = extract_shares(args.unknown_shares_file)

    secrets = np.zeros(args.field_modulo)
    Mod.set_mod(args.field_modulo)
    for shares_prod in itertools.product(*known_shares_col):
        for i, share in enumerate(unknown_shares):
            stdout.write(f'i={i}/{unknown_mod}\r')
            res = garner_algorithm(shares_prod + (share, ),
                                   known_mods + (unknown_mod, ))
            secrets[Mod(res).value] += 1

    fp = np.memmap(f'{args.field_modulo}.dat',
                   dtype=np.int64,
                   mode='w+',
                   shape=np.size(secrets))
    fp[:] = secrets[:]  # copy all values
    fp.flush()


if __name__ == '__main__':
    main()
