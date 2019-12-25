import itertools
import random
from timeit import default_timer as timer

import numpy as np
from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import add_state_features, Tags

###################################################################################################
from polymod import PolyMod, Mod


def print_done(start_val):
    global elapsed
    elapsed = timer() - start_val
    print('< done, time elapsed: [{:.2f}] seconds'.format(elapsed))


def print_start(msg):
    print('> starting {:s}...'.format(msg))


def generate_data():
    # states = range(1, 10)
    # transitions = dict()
    # for src in states:
    #     transitions[src] = (
    #         {0: random.choice(states), 1: random.choice(states)},
    #         random.randint(0, 1)
    #     )
    states = {
        100: 211,
        200: 223,
        300: 227,
        400: 229,
    }
    transitions = {
        100: ({1: 100, 2: 200, 3: 400, 4: 300}, random.randint(0, 1)),
        200: ({1: 100, 2: 300, 3: 400, 4: 200}, random.randint(0, 1)),
        300: ({1: 300, 2: 200, 3: 100, 4: 400}, random.randint(0, 1)),
        400: ({1: 200, 2: 300, 3: 400, 4: 100}, random.randint(0, 1)),
    }

    return states, transitions


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    # parser.add_argument('polynomial')
    args = parser.parse_args()

    # crr = CRR(*np.array([8, 7, 5], dtype="uint8"))
    # x_vec = np.array([3, 2, 1], dtype="uint8")
    # y_vec = np.array([5, 5, 0], dtype="uint8")
    # print(crr.add(x_vec, y_vec))
    # print(crr.mul(x_vec, y_vec))

    print_start('state machine data generation')
    start = timer()
    states, transitions = generate_data()

    xy_s = itertools.chain(*[
        [(src + i, t[0].get(1)) for i in [1, 2, 3, 4]]
        # [(src + 1, t[0].get(1)), (src + 2, t[0].get(2)), (src + 3, t[0].get(3)), (src + 4, t[0].get(4))]
        for src, t in transitions.items()])

    primes = [states[k] for k in transitions.keys()]
    product = np.prod(primes, dtype=np.int64)
    Mod.set_mod(int(product))
    p = PolyMod.interpolate(list(xy_s))
    # print('p={:s} (mod {:d})'.format(str(p), product))
    for prime in primes:
        Mod.set_mod(prime)
        pp = PolyMod([int(str(t)) for t in p.terms])
        print('pp={:s} (mod {:d})'.format(str(pp), prime))

    elapsed = timer() - start
    print_done(start)

    # primes = [37, 47, 67]
    # print('Find y={:d} for x={:d} while P={:d}'.format(y_s[9], x_s[9], primes[0] * primes[1] * primes[2]))
    # y0 = shamir._lagrange_interpolate(x_s[9] % primes[0], np.mod(x_s, primes[0]), np.mod(y_s, primes[0]), primes[0])
    # print('y={:d} (mod {:d})'.format(y0, primes[0]))
    # y1 = shamir._lagrange_interpolate(x_s[9] % primes[1], np.mod(x_s, primes[1]), np.mod(y_s, primes[1]), primes[1])
    # print('y={:d} (mod {:d})'.format(y1, primes[1]))
    # y2 = shamir._lagrange_interpolate(x_s[9] % primes[2], np.mod(x_s, primes[2]), np.mod(y_s, primes[2]), primes[2])
    # print('y={:d} (mod {:d})'.format(y2, primes[2]))
    # print_done(start)

    print_start('state machine drawing')
    start = timer()


    @add_state_features(Tags)
    class CustomStateMachine(Machine):
        pass


    class Matter(object):
        pass


    lump = Matter()
    m = CustomStateMachine(
        model=lump,
        states=[
            {'name': str(src), 'tags': ['out: {:d}'.format(trans[1])]} for src, trans in transitions.items()
        ],
        transitions=[{'trigger': 'in: {:d}'.format(1),
                      'source': str(src),
                      'dest': str(trans[0].get(1)),
                      'after': str(trans[1])}
                     for src, trans in transitions.items()] +
                    [{'trigger': 'in: {:d}'.format(2),
                      'source': str(src),
                      'dest': str(trans[0].get(2)),
                      'after': str(trans[1])}
                     for src, trans in transitions.items()] +
                    [{'trigger': 'in: {:d}'.format(3),
                      'source': str(src),
                      'dest': str(trans[0].get(3)),
                      'after': str(trans[1])}
                     for src, trans in transitions.items()] +
                    [{'trigger': 'in: {:d}'.format(4),
                      'source': str(src),
                      'dest': str(trans[0].get(4)),
                      'after': str(trans[1])}
                     for src, trans in transitions.items()],
        initial=str(list(states.keys())[0]),
        show_state_attributes=True
    )
    m.get_graph().draw('diagram.png', prog='dot')

    elapsed = timer() - start
    print_done(start)

    start = timer()
