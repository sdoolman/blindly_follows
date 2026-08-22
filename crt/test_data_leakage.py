"""Test script for measuring data leakage across CRT shares."""

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np

from polynomials.polymod import Mod
from secret_sharing.mathlib import garner_algorithm


def extract_shares(shares_path: Path | str) -> tuple[np.ndarray, int]:
    """Extract non-zero shares and size from a binary memory map file."""
    path = Path(shares_path)
    if not path.exists():
        raise FileNotFoundError(f"Share file not found: {path}")
    freq = np.memmap(path, mode="r", dtype=np.int64)
    return np.where(freq != 0)[0], int(np.size(freq))


def compute_leakage(
    known_files: list[Path | str],
    unknown_file: Path | str,
    field_modulo: int,
    output_file: Path | str | None = None,
) -> Path:
    """Compute and persist data leakage distribution."""
    known_shares_col, known_mods = zip(*(extract_shares(sf) for sf in known_files))
    unknown_shares, unknown_mod = extract_shares(unknown_file)

    secrets = np.zeros(field_modulo, dtype=np.int64)
    Mod.set_mod(field_modulo)

    for shares_prod in itertools.product(*known_shares_col):
        for i, share in enumerate(unknown_shares):
            sys.stdout.write(f"i={i}/{unknown_mod}\r")
            res = garner_algorithm(
                shares_prod + (share,),
                known_mods + (unknown_mod,),
            )
            secrets[Mod(res).value] += 1

    out_path = Path(output_file or f"{field_modulo}.dat")
    fp = np.memmap(out_path, dtype=np.int64, mode="w+", shape=np.size(secrets))
    fp[:] = secrets[:]
    fp.flush()
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze CRT data leakage")
    parser.add_argument("known_shares_files", nargs="+", type=Path, metavar="MOD.dat")
    parser.add_argument("unknown_shares_file", type=Path, metavar="MOD.dat")
    parser.add_argument("field_modulo", type=int)

    args = parser.parse_args()
    compute_leakage(
        args.known_shares_files,
        args.unknown_shares_file,
        args.field_modulo,
    )


if __name__ == "__main__":
    main()
