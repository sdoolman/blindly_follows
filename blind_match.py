from bitstring import BitArray

T = [
    (BitArray(bin='101001'), BitArray(bin='101010')),
    (BitArray(bin='010110'), BitArray(bin='010101')),
]  # must be hashable


def match(x: str) -> str:
    x = BitArray(bin=x)
    res = BitArray(length=len(x))
    for current_state, next_state in T:
        tmp = BitArray(bin='1')
        for i in range(len(x))[::2]:
            tmp = tmp & BitArray(bool=x[i] & current_state[i]
                                 | x[i + 1] & current_state[i + 1])
        res |= (tmp * len(next_state)) & next_state

    return res.bin


def main():
    print('> transition table is:\n' + '\n'.join(f'{x} --> {y}' for x, y in T))
    x = input('> enter state: ')
    try:
        print(f'next state is: {match(x)}')
    except ValueError as e:
        print(f'invalid state, error: [{e}]')


if __name__ == '__main__':
    main()
