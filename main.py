import itertools
import multiprocessing
import random
from timeit import default_timer as timer

import numpy as np
from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import add_state_features, Tags

###################################################################################################
from crr import mathlib
from crr.generic_functions import get_ab_share, get_primes
from polymod import PolyMod, Mod


def print_done(start_val):
    elapsed = timer() - start_val
    print('< done! time elapsed: [{:.2f}] seconds'.format(elapsed))


def print_start(msg):
    print('> starting {:s}...'.format(msg))


def generate_data():
    # {q1:100,q2:200,q3:300,q4:400}
    # {0:0,1:1,b:2,br:3,bl:4,c:5}
    data = dict(
        [(k, (dict(), random.randint(0, 1)))
         for k in {100, 200, 300, 400}]
    )

    data[100][0].update({14: 100, 23: 100, 32: 100, 40: 100, 4: 100, 50: 400})
    data[200][0].update({10: 200, 23: 300, 34: 200, 43: 200, 1: 200, 52: 200})
    data[300][0].update({11: 300, 24: 400, 32: 300, 5: 100, 51: 100})
    data[400][0].update({10: 400, 25: 200, 34: 400, 5: 200, 52: 400})

    return data


def main1():
    def f(terms, mod, current_state, inputs, results_out):
        Mod.set_mod(mod)
        poly = PolyMod(terms)
        print(f'polynomial is: {str(poly)} (mod {mod})')

        for i in inputs:
            current_state = poly(current_state + i).value

        # print(f'current state is: {current_state} (mod {mod})')
        results_out.put((current_state, mod))

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

    ms = get_primes(xy_s)
    print(f'co-prime sequence is: m0={ms[0]}, m={ms[1:]}')

    product = np.prod(list(ms[1:]), dtype=np.int64)
    Mod.set_mod(int(product))
    p = PolyMod.interpolate(xy_s)

    print_done(start)

    print_start('assigning jobs')
    start = timer()

    # print('p={:s} (mod {:d})'.format(str(p), product))
    initial_state = get_ab_share(2, ms[:])
    inputs = [get_ab_share(i, ms[:]) for i in [23, 24, 25]]
    jobs = list()
    results_queue = multiprocessing.SimpleQueue()
    for m in ms[1:4]:
        Mod.set_mod(m)
        job = multiprocessing.Process(target=f, args=(
            [t.value for t in p.terms],
            m,
            Mod(initial_state),
            [Mod(i) for i in inputs],
            results_queue))
        jobs.append(job)
        job.start()

    print_done(start)

    print_start('collecting results')
    start = timer()

    results = list()
    for job in jobs:
        job.join()
        results += [results_queue.get()]

    Mod.set_mod(ms[0])
    next_state = Mod(mathlib.garner_algorithm([x for x, _ in results], [x for _, x in results]))
    print(f'next state is: [{next_state.value}]!')

    print_done(start)

    print_start('drawing state machine')
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


def main2():
    def f(terms, mod, current_state, inputs, results_out):
        Mod.set_mod(mod)
        poly = PolyMod(terms)
        print(f'polynomial is: {str(poly)} (mod {mod})')

        for i in inputs:
            current_state = poly(current_state + i).value

        # print(f'current state is: {current_state} (mod {mod})')
        results_out.put((current_state, mod))

    ms = [3, 11, 13, 17, 19]
    initial_state = get_ab_share(2, ms[:])
    inputs = [get_ab_share(i, ms[:]) for i in [23, 24, 25]]
    jobs = list()
    results_queue = multiprocessing.SimpleQueue()
    for m in ms[1:4]:
        Mod.set_mod(m)
        job = multiprocessing.Process(target=f, args=(
            None,  # [t.value for t in p.terms],
            m,
            Mod(initial_state),
            [Mod(i) for i in inputs],
            results_queue))
        jobs.append(job)
        job.start()


if __name__ == '__main__':
    main2()
