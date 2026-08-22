"""Blind state matching over bit-array transition tables."""

from bitstring import BitArray

TRANSITION_TABLE: list[tuple[BitArray, BitArray]] = [
    (BitArray(bin="101001"), BitArray(bin="101010")),
    (BitArray(bin="010110"), BitArray(bin="010101")),
]


def match(state_bin: str) -> str:
    """Evaluate next state over masked binary state table without revealing branches."""
    x = BitArray(bin=state_bin)
    res = BitArray(length=len(x))
    for current_state, next_state in TRANSITION_TABLE:
        tmp = BitArray(bin="1")
        for i in range(0, len(x), 2):
            bit_match = (x[i] & current_state[i]) | (x[i + 1] & current_state[i + 1])
            tmp = tmp & BitArray(bool=bit_match)
        res |= (tmp * len(next_state)) & next_state

    return res.bin


def main() -> None:
    print(
        "> transition table is:\n"
        + "\n".join(f"{x} --> {y}" for x, y in TRANSITION_TABLE)
    )
    x = input("> enter state (e.g. 101001): ").strip()
    try:
        print(f"next state is: {match(x)}")
    except ValueError as e:
        print(f"invalid state, error: [{e}]")


if __name__ == "__main__":
    main()
