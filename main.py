import itertools
import random
from multiprocessing import Process
from timeit import default_timer as timer

import numpy as np
from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import add_state_features, Tags

###################################################################################################
from crr.generic_functions import get_primes
from polymod import PolyMod, Mod


def print_done(start_val):
    elapsed = timer() - start_val
    print('< done, time elapsed: [{:.2f}] seconds'.format(elapsed))


def print_start(msg):
    print('> starting {:s}...'.format(msg))


def generate_data():
    # {q1:100,q2:200,q3:300,q4:400}
    # {0:0,1:1,b:2,br:3,bl:4,c:5}
    inputs = {14, 23, 24, 25, 32, 34, 40, 43, 50, 51, 52}
    # data = dict(
    #     [(k, (dict([(i, k) for i in inputs]), random.randint(0, 1)))
    #      for k in {100, 200, 300, 400}]
    # )
    data = dict(
        [(k, (dict(), random.randint(0, 1)))
         for k in {100, 200, 300, 400}]
    )

    data[100][0].update({14: 100, 23: 100, 32: 100, 40: 100, 4: 100, 50: 400})
    data[200][0].update({10: 200, 23: 300, 34: 200, 43: 200, 1: 200, 52: 200})
    data[300][0].update({11: 300, 24: 400, 32: 300, 5: 100, 51: 100})
    data[400][0].update({10: 400, 25: 200, 34: 400, 5: 200, 52: 400})

    return data


def f(terms, mod, inputs):
    Mod.set_mod(mod)
    poly = PolyMod(terms)
    print(f'polynomial is: {str(poly)} (mod {mod})')
    # print(f'polynomial is: {[int(t.value) for t in poly.terms]} (mod {mod})')
    current_state = 200  # TODO: currently starting from 200

    for i in inputs:
        current_state = poly(current_state + i).value

    print(f'current state is: {current_state} (mod {mod})')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print_start('state machine data generation')
    start = timer()
    transitions = generate_data()

    xy_s = itertools.chain(*[
        [(src + i, t[0].get(i)) for i in t[0].keys()]
        for src, t in transitions.items()])
    xy_s = list(xy_s)

    print_done(start)

    print_start('interpolating polynomial')
    start = timer()

    primes = get_primes(xy_s)
    print(f'co-prime sequence is: {primes}')

    product = np.prod(list(primes), dtype=np.int64)
    Mod.set_mod(int(product))
    p = PolyMod.interpolate(xy_s)

    print_done(start)

    print_start('assigning jobs')
    start = timer()

    # print('p={:s} (mod {:d})'.format(str(p), product))

    jobs = list()
    for prime in primes:
        Mod.set_mod(prime)
        job = Process(target=f, args=([int(str(t)) for t in p.terms], prime, [23, 24, 25]))
        jobs.append(job)
        job.start()

    for job in jobs:
        job.join()

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
        initial=str(200),
        show_state_attributes=True
    )
    m.get_graph().draw('diagram.png', prog='dot')

    print_done(start)

    start = timer()
