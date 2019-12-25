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
    states = {
        100: 113,
        200: 127,
        300: 137,
        400: 149,
    }
    # {q1:100,q2:200,q3:300,q4:400}
    # {0:0,1:1,b:2,br:3,bl:4,c:5}
    transitions = {
        100: ({14: 100, 23: 100, 32: 100, 40: 100, 4: 100, 50: 400}, random.randint(0, 1)),
        200: ({10: 200, 23: 300, 34: 200, 43: 200, 1: 200, 52: 200}, random.randint(0, 1)),
        300: ({11: 300, 24: 400, 32: 300, 5: 100, 51: 100}, random.randint(0, 1)),
        400: ({10: 400, 25: 200, 34: 400, 5: 200, 52: 400}, random.randint(0, 1)),
    }

    return states, transitions


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print_start('state machine data generation')
    start = timer()
    states, transitions = generate_data()

    xy_s = itertools.chain(*[
        [(src + i, t[0].get(i)) for i in t[0].keys()]
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
        transitions=list(itertools.chain(*[
            [{'trigger': 'in: {:d}'.format(i),
              'source': str(src),
              'dest': str(t[0].get(i)),
              'after': str(t[1])
              } for i in t[0].keys()]
            for src, t in transitions.items()])),
        initial=str(list(states.keys())[0]),
        show_state_attributes=True
    )
    m.get_graph().draw('diagram.png', prog='dot')

    elapsed = timer() - start
    print_done(start)

    start = timer()
