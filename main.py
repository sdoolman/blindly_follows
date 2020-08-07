#!/usr/bin/python3
import hashlib
import itertools
import json
import multiprocessing
import pickle
import random
import string
import sys
from datetime import datetime
from timeit import default_timer as timer

import matplotlib
import numpy as np

matplotlib.use('Agg')
from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import add_state_features, Tags

from crr import mathlib
from crr.generic_functions import get_ab_share, get_mignotte_params
from polymod import PolyMod, Mod

###################################################################################################
RANDOM_INPUT_LENGTH = 1 * 1024 ** 2
QUEUE_MAX_SIZE = 1024


def print_done(start_val):
    elapsed = timer() - start_val
    print('< done! time elapsed: [{:.2f}] seconds'.format(elapsed))


def print_start(msg):
    print('> starting {:s}...'.format(msg))


def value(character):
    specials = {
        '.': 27,
        ' ': 28,
        '\n': 29,
    }
    if character in specials:
        return specials[character]
    elif character in string.ascii_letters:
        return ord(character.lower()) - ord('`')
    else:
        raise Exception(f'failed to find value of [{character}] - consider adding support for it')


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

    data[0][0].update({value(c): 0 for c in string.ascii_lowercase + '. \n'})
    data[100][0].update({value(c): 0 for c in string.ascii_lowercase + '. \n'})
    data[200][0].update({value(c): 0 for c in string.ascii_lowercase + '. \n'})
    data[300][0].update({value(c): 0 for c in string.ascii_lowercase + '. \n'})
    data[400][0].update({value(c): 400 for c in string.ascii_lowercase + '. \n'})

    data[0][0].update({value('n'): 100})
    data[100][0].update({value('n'): 100})
    data[100][0].update({value('a'): 200})
    data[200][0].update({value('n'): 300})
    data[300][0].update({value('o'): 400})
    data[300][0].update({value('n'): 100})
    data[300][0].update({value('a'): 200})

    return data


def f1(poly, mod, current_state, input_q, results_out, queue_exhausted):
    Mod.set_mod(mod)

    next_state = current_state
    while not (queue_exhausted.is_set() and input_q.empty()):
        item = input_q.get(block=True)
        # print(f'[{mod}] item=[{item}]')
        next_state = poly(next_state + item).value  # modulo will already be applied here
        input_q.task_done()

    print(f'[{mod}] next state=[{next_state}]')

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

    print_start('mignotte parameters calculation')
    start = timer()

    n, k = 3, 3
    ms = get_mignotte_params(xy_s)
    print(f'ms={ms}')
    print_done(start)

    print_start('polynomial interpolation')
    start = timer()

    Mod.set_mod(int(np.prod(ms, dtype=np.int64)))
    try:
        with open('p.bin', 'rb') as f:
            p = pickle.load(f)
    except FileNotFoundError:
        p = PolyMod.interpolate([(x, y) for x, y in xy_s.items()])
        with open('p.bin', 'wb') as f:
            pickle.dump(p, f)
    print(f'p={str(p)}')

    print_done(start)

    print_start('jobs assignment')
    start = timer()

    # print('p={:s} (mod {:d})'.format(str(p), product))
    initial_state = 0
    processes = dict()
    results_q = multiprocessing.SimpleQueue()
    exhausted = multiprocessing.Event()
    for mod in ms[:k]:
        Mod.set_mod(mod)
        input_q = multiprocessing.JoinableQueue(maxsize=QUEUE_MAX_SIZE)
        process = multiprocessing.Process(target=f1, args=(
            p,
            mod,
            initial_state,
            input_q,
            results_q,
            exhausted))
        processes[mod] = (process, input_q)
        process.start()

    print_done(start)

    print_start('file parsing')
    start = timer()

    sequence_length = 100
    sequences = RANDOM_INPUT_LENGTH // sequence_length
    for si in range(sequences):
        random_chars = random.choices(string.ascii_lowercase + '. ', k=random.randrange(sequence_length))
        inputs = [value(c) for c in (random_chars if random.randint(0, 100) != 0 else 'nano')]
        for mod, (_, input_q) in processes.items():
            Mod.set_mod(mod)
            for i in inputs:
                input_q.put(i, block=True)
        sys.stdout.write(f'{si}/{sequences}\r')
    print_done(start)

    print_start('final results collection')
    start = timer()

    exhausted.set()
    results = list()
    for mod, (_, input_q) in processes.items():
        sys.stdout.write(f'waiting for [{mod}] to complete...\r')
        input_q.join()
        results += [results_q.get()]

    next_state = mathlib.garner_algorithm([x for x, _ in results], [x for _, x in results])
    print(f'next state is: [{next_state}]!')

    print_done(start)

    print_start('state machine drawing')
    start = timer()

    @add_state_features(Tags)
    class CustomStateMachine(Machine):
        pass

    class Matter(object):
        pass

    lump = Matter()
    fsm = CustomStateMachine(
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
    fsm.get_graph().draw('diagram.png', prog='dot')

    print_done(start)


def main2():
    m0 = 11 * 13 * 17
    ms = [17 * 223, 13 * 227, 11 * 229]
    freq = {
        m: np.zeros(m) for m in ms
    }
    expected = hashlib.sha256()
    actual = hashlib.sha256()
    for _ in range(10 ** 6):
        i = random.randint(1, 10)
        expected.update(chr(i).encode())
        share = get_ab_share(i, m0, ms)
        shares = list()
        for m in ms:
            Mod.set_mod(m)
            v = PolyMod([2, 3])(share).value
            shares += [v]
            freq[m][v] += 1
        from crr.mathlib import garner_algorithm
        Mod.set_mod(m0)
        v = ((Mod(garner_algorithm(shares, ms)) - 2) * Mod(3).inverse()).value
        actual.update(chr(v).encode())
    from matplotlib import pyplot as plt
    for m in freq:
        max_freq = np.max(freq[m])
        fig, (ax1, ax2) = plt.subplots(2)
        fig.suptitle(f'mod={m}')
        ax1.plot(np.arange(m), freq[m], 'b.', markersize=1)
        ax1.set_yticks(np.arange(0, max_freq + 1, 100))
        ax2.hist(freq[m])
        ax2.set_yscale("log")
        ax2.set_xticks(np.arange(0, max_freq + 1, 100))
        plt.savefig(f'{m}.png')
        plt.close()

    print(f'expected=[{expected.hexdigest()}]\n  actual=[{actual.hexdigest()}]')


def main3():
    m0 = 11 * 13 * 17
    ms = [17 * 223, 13 * 227, 11 * 229]

    inp = 14
    share = get_ab_share(inp, m0, ms)
    shares = list()

    for m in ms[:-1]:
        Mod.set_mod(m)
        shares += [Mod(share).value]

    freq = np.zeros(ms[-1])
    for i in range(ms[-1]):
        Mod.set_mod(ms[-1])
        shares += [Mod(i).value]
        Mod.set_mod(m0)
        from crr.mathlib import garner_algorithm
        v = Mod(garner_algorithm(shares, ms)).value
        freq[v] += 1
        shares.pop()

    with open(f'{datetime.now().strftime("%H%M%S")}.json', 'w') as f:
        json.dump(freq.tolist(), f)


if __name__ == '__main__':
    main1()
    sys.exit(0)
