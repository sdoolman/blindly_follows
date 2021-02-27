from bitstring import BitArray

T = [
    (BitArray(bin='101001'), BitArray(bin='101010')),
    (BitArray(bin='010110'), BitArray(bin='010101')),
]


def match(x: str) -> str:
    x = BitArray(bin=x)
    res = BitArray(length=len(x))
    for k, v in T:
        tmp = BitArray(bin='1')
        for i in range(len(x))[::2]:
            tmp = tmp & BitArray(bool=((x[i] & k[i]) | (x[i + 1] & k[i + 1])))
        res |= (tmp * len(v)) & v

    return res.bin
