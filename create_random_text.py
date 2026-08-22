#!/usr/bin/env python3
"""Utility script for generating random text input files for testing."""

import random
import string
from pathlib import Path

from progressbar import progressbar

LINE_LENGTH: int = 100
FILE_LENGTH: int = 50 * 1024**2


def generate_random_file(
    output_path: Path | str = "some_text.txt",
    file_length: int = FILE_LENGTH,
    max_line_length: int = LINE_LENGTH,
) -> None:
    """Generate a file with random ASCII text lines."""
    target = Path(output_path)
    number_of_lines = file_length // max_line_length
    charset = string.ascii_letters + ". "

    with target.open("w", encoding="utf-8") as f:
        for _ in progressbar(range(number_of_lines)):
            line_len = random.randrange(max_line_length)
            line = "".join(random.choices(charset, k=line_len))
            f.write(f"{line}\n")
    print(f"Done generating {target} ({file_length} bytes)!")


def main() -> None:
    generate_random_file()


if __name__ == "__main__":
    main()
