"""Mathematical library for modular arithmetic, primality testing, and CRT."""

import random
from collections.abc import Iterator, Sequence

_random = random.SystemRandom()

_small_odd_primes: list[int] = [
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
    71,
    73,
    79,
    83,
    89,
    97,
    101,
    103,
    107,
    109,
    113,
    127,
    131,
    137,
    139,
    149,
    151,
    157,
    163,
    167,
    173,
    179,
    181,
    191,
    193,
    197,
    199,
    211,
    223,
    227,
    229,
    233,
    239,
    241,
    251,
    257,
    263,
    269,
    271,
    277,
    281,
    283,
    293,
    307,
    311,
    313,
    317,
    331,
    337,
    347,
    349,
    353,
    359,
    367,
    373,
    379,
    383,
    389,
    397,
    401,
    409,
    419,
    421,
    431,
    433,
    439,
    443,
    449,
    457,
    461,
    463,
    467,
    479,
    487,
    491,
    499,
    503,
    509,
    521,
    523,
    541,
    547,
    557,
    563,
    569,
    571,
    577,
    587,
    593,
    599,
    601,
    607,
    613,
    617,
    619,
    631,
    641,
    643,
    647,
    653,
    659,
    661,
    673,
    677,
    683,
    691,
    701,
    709,
    719,
    727,
    733,
    739,
    743,
    751,
    757,
    761,
    769,
    773,
    787,
    797,
    809,
    811,
    821,
    823,
    827,
    829,
    839,
    853,
    857,
    859,
    863,
    877,
    881,
    883,
    887,
    907,
    911,
    919,
    929,
    937,
    941,
    947,
    953,
    967,
    971,
    977,
    983,
    991,
    997,
    1009,
    1013,
    1019,
    1021,
    1031,
    1033,
    1039,
    1049,
    1051,
    1061,
    1063,
    1069,
    1087,
    1091,
    1093,
    1097,
    1103,
    1109,
    1117,
    1123,
    1129,
    1151,
    1153,
    1163,
    1171,
    1181,
    1187,
    1193,
    1201,
    1213,
    1217,
    1223,
    1229,
    1231,
    1237,
    1249,
    1259,
    1277,
    1279,
    1283,
    1289,
    1291,
    1297,
    1301,
    1303,
    1307,
    1319,
    1321,
    1327,
    1361,
    1367,
    1373,
    1381,
    1399,
    1409,
    1423,
    1427,
    1429,
    1433,
    1439,
    1447,
    1451,
    1453,
    1459,
    1471,
    1481,
    1483,
    1487,
    1489,
    1493,
    1499,
    1511,
    1523,
    1531,
    1543,
    1549,
    1553,
    1559,
    1567,
    1571,
    1579,
    1583,
    1597,
    1601,
    1607,
    1609,
    1613,
    1619,
    1621,
    1627,
    1637,
    1657,
    1663,
    1667,
    1669,
    1693,
    1697,
    1699,
    1709,
    1721,
    1723,
    1733,
    1741,
    1747,
    1753,
    1759,
    1777,
    1783,
    1787,
    1789,
    1801,
    1811,
    1823,
    1831,
    1847,
    1861,
    1867,
    1871,
    1873,
    1877,
    1879,
    1889,
    1901,
    1907,
    1913,
    1931,
    1933,
    1949,
    1951,
    1973,
    1979,
    1987,
    1993,
    1997,
    1999,
    2003,
    2011,
    2017,
    2027,
    2029,
    2039,
    2053,
]

_miller_rabin_rounds: dict[int, int] = {
    150: 27,
    200: 18,
    250: 15,
    300: 12,
    350: 9,
    400: 8,
    450: 7,
    550: 6,
    650: 5,
    850: 4,
    1250: 3,
}


def bit_len(n: int) -> int:
    """Return size of n in bits."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return n.bit_length()


def get_random_range(a: int, b: int) -> int:
    """Return random integer between a and b."""
    if a > b:
        a, b = b, a
    return _random.randint(a + 1, b - 1) if b - a > 1 else a


def _get_mr_rounds(k: int) -> int:
    """Return number of Miller-Rabin rounds for k-bit length."""
    for b_len, rounds in sorted(_miller_rabin_rounds.items()):
        if k < b_len:
            return rounds
    return 2


def miller_rabin_test(n: int, rounds: int) -> bool:
    """Miller-Rabin primality test. Returns True if n is probably prime."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    r, s = n - 1, 0
    while r % 2 == 0:
        r //= 2
        s += 1

    for _ in range(rounds):
        a = _random.randint(2, n - 2)
        y = pow(a, r, n)
        if y != 1 and y != n - 1:
            for _ in range(s - 1):
                y = (y * y) % n
                if y == n - 1:
                    break
            else:
                return False
    return True


def sieve_test(n: int) -> bool:
    """Check if n is divisible by any precomputed small primes."""
    for prime in _small_odd_primes:
        if n % prime == 0:
            return n == prime
    return True


def combined_sieve_test(n: int) -> bool:
    """Check if n and p = 2*n + 1 are good Sophie Germain prime candidates."""
    p = (n << 1) | 1
    if (p % 3 == 2 and n % 3 == 2) or p == 7:
        for prime in _small_odd_primes:
            if n % prime == 0 and n % prime == ((prime - 1) >> 1) % prime:
                return n == prime
        return True
    return False


def primality_test(n: int) -> bool:
    """Perform primality test for n."""
    if n & 1:
        rounds = _get_mr_rounds(bit_len(n))
        return sieve_test(n) and miller_rabin_test(n, rounds)
    return n == 2


def primality_test_for_sg_prime(n: int) -> bool:
    """Primality test for Sophie Germain prime n (where p = 2*n + 1 is also prime)."""
    if n & 1 and combined_sieve_test(n):
        p = (n << 1) | 1
        n_rounds = _get_mr_rounds(bit_len(n))
        p_rounds = _get_mr_rounds(bit_len(p))
        return miller_rabin_test(n, n_rounds) and miller_rabin_test(p, p_rounds)
    return False


def get_prime(k: int) -> int:
    """Generate k-bit random prime number."""
    while True:
        p = _random.getrandbits(k) | (1 << (k - 1)) | 1
        if primality_test(p):
            return p


def get_sg_prime(k: int) -> int:
    """Generate k-bit random Sophie Germain prime number."""
    while True:
        n = _random.getrandbits(k) | (1 << (k - 1)) | 1
        if primality_test_for_sg_prime(n):
            return n


def get_consecutive_primes(n: int, k: int) -> Iterator[int]:
    """Generate n consecutive primes starting from a k-bit prime."""
    m = get_prime(k)
    yield m
    count = n - 1
    while count > 0:
        m += 2
        if primality_test(m):
            yield m
            count -= 1


def get_consecutive_sg_primes(n: int, k: int) -> Iterator[int]:
    """Generate n consecutive Sophie Germain primes starting from a k-bit prime."""
    m = get_sg_prime(k)
    yield m
    count = n - 1
    while count > 0:
        m += 6
        if primality_test_for_sg_prime(m):
            yield m
            count -= 1


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Extended Euclidean algorithm. Returns (u, v, gcd)."""
    u, u1 = 1, 0
    v, v1 = 0, 1
    g, g1 = a, b
    while g1:
        q = g // g1
        u, u1 = u1, u - q * u1
        v, v1 = v1, v - q * v1
        g, g1 = g1, g - q * g1
    return u, v, g


def multiplicative_inverse(a: int, b: int) -> int:
    """Calculate multiplicative inverse of a modulo b via Extended Euclidean Algorithm."""
    m, _, _ = extended_gcd(a, b)
    if m < 0:
        m = m % b
    return m


def garner_algorithm(v: Sequence[int], m: Sequence[int]) -> int:
    """Garner's algorithm for reconstructing integer value from CRT modular shares."""
    num_mods = len(m)
    c_coeffs = [0] * num_mods
    for i in range(1, num_mods):
        c_coeffs[i] = 1
        for j in range(i):
            u = multiplicative_inverse(m[j], m[i])
            c_coeffs[i] = (u * c_coeffs[i]) % m[i]

    u = v[0]
    x = u
    for i in range(1, num_mods):
        u = ((v[i] - x) * c_coeffs[i]) % m[i]
        s = 1
        for j in range(i):
            s *= m[j]
        x += u * s
    return x
