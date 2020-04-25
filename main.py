import itertools
import multiprocessing
import random
import string
import sys
from timeit import default_timer as timer

from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import add_state_features, Tags

###################################################################################################
from crr import mathlib
from crr.generic_functions import get_ab_share, get_ab_params, get_ab_sequence, M0
from polymod import PolyMod, Mod


def print_done(start_val):
    elapsed = timer() - start_val
    print('< done! time elapsed: [{:.2f}] seconds'.format(elapsed))


def print_start(msg):
    print('> starting {:s}...'.format(msg))


def value(character):
    whitespace = {
        ' ': 27,
        '\n': 28
    }
    if character in string.whitespace:
        return whitespace[character]
    else:
        return ord(character) - ord('`')


def generate_data():
    # {q1:100,q2:200,q3:300,q4:400}
    # {0:0,1:1,b:2,br:3,bl:4,c:5}
    # data = dict(
    #     [(k, (dict(), random.randint(0, 1)))
    #      for k in {100, 200, 300, 400}]
    # )
    #
    # data[100][0].update({14: 100, 23: 100, 32: 100, 40: 100, 4: 100, 50: 400})
    # data[200][0].update({10: 200, 23: 300, 34: 200, 43: 200, 1: 200, 52: 200})
    # data[300][0].update({11: 300, 24: 400, 32: 300, 5: 100, 51: 100})
    # data[400][0].update({10: 400, 25: 200, 34: 400, 5: 200, 52: 400})
    data = {
        k: (dict(), random.randint(0, 1))
        for k in {0, 100, 200, 300, 400}
    }

    data[0][0].update({value(c): 0 for c in string.ascii_lowercase + ' \n'})
    data[100][0].update({value(c): 0 for c in string.ascii_lowercase + ' \n'})
    data[200][0].update({value(c): 0 for c in string.ascii_lowercase + ' \n'})
    data[300][0].update({value(c): 0 for c in string.ascii_lowercase + ' \n'})
    data[400][0].update({value(c): 400 for c in string.ascii_lowercase + ' \n'})

    data[0][0].update({value('n'): 100})
    data[100][0].update({value('n'): 100})
    data[100][0].update({value('a'): 200})
    data[200][0].update({value('n'): 300})
    data[300][0].update({value('o'): 400})
    data[300][0].update({value('n'): 100})
    data[300][0].update({value('a'): 200})

    return data


def f1(poly, mod, current_state, inputs, results_out):
    Mod.set_mod(mod)

    next_state = current_state
    for i in inputs:
        current_state = (next_state + i).value
        next_state = poly(current_state).value

    print(f'next state is: {next_state} (mod {mod})')
    results_out.put((next_state, mod))


def main1():
    import argparse

    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print_start('state machine data generation')
    start = timer()
    transitions = generate_data()

    xy_s = {x: y for (x, y) in
            itertools.chain.from_iterable(
                [(src + i, t[0].get(i)) for i in t[0].keys()]
                for src, t in transitions.items())}

    print_done(start)

    print_start('ab parameters calculation')
    start = timer()

    n, k = 4, 3
    m0, ms = get_ab_params(xy_s)
    print(f'm0={m0}, ms={ms}')
    print_done(start)

    Mod.set_mod(m0)

    print_start('polynomial interpolation')
    start = timer()
    p = PolyMod.interpolate([(x, y) for x, y in xy_s.items()])
    print(f'p={str(p)}')

    print_done(start)

    print_start('assigning jobs')
    start = timer()

    # print('p={:s} (mod {:d})'.format(str(p), product))
    initial_state = get_ab_share(100, m0, ms[:k])
    with open('some_text.txt', 'r') as f:
        content = f.read()
    inputs = [get_ab_share(value(c), m0, ms[:]) for c in content]
    jobs = list()
    results_queue = multiprocessing.SimpleQueue()
    for m in ms[:k]:
        job = multiprocessing.Process(target=f1, args=(
            p,
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

    Mod.set_mod(m0)
    next_state = Mod(mathlib.garner_algorithm([x for x, _ in results], [x for _, x in results])).value
    print(f'next state is: [{next_state}]!')

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


def main3():
    def successive(x, times):
        if times == 0:
            return x
        # sys.stdout.write(f'({Mod(x).value}, {poly(x).value}),\n')
        return successive(poly(x).value, times - 1)

    sys.setrecursionlimit(1500)

    m0 = M0(53, 71, 89)
    print(f'm0={m0.value}')
    n, k = 4, 3
    ms = get_ab_sequence(m0, limit=7000, n=n, k=k)  # this should work
    print(f'ms={ms}')

    initial_state = 33
    print(f'input={initial_state}')

    secret = get_ab_share(initial_state, [m0.value] + ms[:k])
    print(f'secret={secret}')

    Mod.set_mod(m0.value)
    poly = PolyMod.interpolate(
        [(299, 11), (19, 326), (11, 287), (77, 89), (112, 264), (287, 19), (326, 112), (46, 77), (151, 7), (221, 217),
         (264, 221), (217, 194), (7, 299), (194, 46), (33, 221), (89, 151)])
    print(f'poly={str(poly)}')
    expected = successive(initial_state, 100)  # only we know the input

    res = list()
    for m in ms[:k]:
        Mod.set_mod(m)
        res += [successive(secret, 100)]
    Mod.set_mod(m0.value)
    recovered = Mod(mathlib.garner_algorithm(res, ms[:3])).value
    print(f'res={list(zip(res, ms))}, expected={expected}, recovered={recovered}')
    assert recovered == expected


if __name__ == '__main__':
    main1()
