import itertools
import matplotlib
import multiprocessing
import numpy as np
import pickle
import random
import string
import time
from timeit import default_timer as timer
from tqdm import tqdm
from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import add_state_features, Tags

from crr.generic_functions import get_mignotte_params
from secret_sharing.mathlib import garner_algorithm
from polynomials.polymod import PolyMod, Mod

matplotlib.use('Agg')

RANDOM_INPUT_LENGTH = 2**15
QUEUE_MAX_SIZE = 100

def print_done(start_val):
    elapsed = timer() - start_val
    print('< done! time elapsed: [{:.2f}] seconds'.format(elapsed))


def print_start(msg):
    print('> starting {:s}...'.format(msg))


def encode(character):
    def encode_inner():
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
            raise Exception(
                f'failed to find value of [{character}] - consider adding support for it'
            )

    return encode_inner() * 2


def generate_data():
    data = {
        k: (dict(), random.randint(0, 1))
        for k in {100, 200, 300, 400, 500}
    }

    data[100][0].update(
        {encode(c): 100
         for c in string.ascii_lowercase + '. \n'})
    data[200][0].update(
        {encode(c): 100
         for c in string.ascii_lowercase + '. \n'})
    data[300][0].update(
        {encode(c): 100
         for c in string.ascii_lowercase + '. \n'})
    data[400][0].update(
        {encode(c): 100
         for c in string.ascii_lowercase + '. \n'})
    data[500][0].update(
        {encode(c): 500
         for c in string.ascii_lowercase + '. \n'})

    data[100][0].update({encode('n'): 200})
    data[200][0].update({encode('n'): 200})
    data[200][0].update({encode('a'): 300})
    data[300][0].update({encode('n'): 400})
    data[400][0].update({encode('o'): 500})
    data[400][0].update({encode('n'): 200})
    data[400][0].update({encode('a'): 300})

    return data


def worker(poly, mod, current_state, input_q, results_q):
    Mod.set_mod(mod)
    next_state = current_state
    while True:
        item = input_q.get(block=True)
        if item is None:  # stop
            input_q.task_done()
            break
        next_state = poly(next_state +
                          item).value  # modulo will already be applied here
        input_q.task_done()

    results_q.put_nowait((next_state, mod))


def main():
    print_start('state machine data generation')
    start = timer()
    transitions = generate_data()

    xy_s = {
        x: y
        for (x, y) in itertools.chain.from_iterable(
            [(src + i, t[0].get(i)) for i in t[0].keys()]
            for src, t in transitions.items())
    }

    print_done(start)

    print_start('mignotte parameters calculation')
    start = timer()

    n, k = 5, 5
    authorized_range, ms = get_mignotte_params(xy_s, n=n, k=k)
    secret = random.choice(authorized_range)
    shares = [(secret % mi, mi) for mi in ms[:k]]
    print(f'shares=' + str([f'{share} (mod {mi})' for share, mi in shares]))
    assert garner_algorithm([x for x, _ in shares],
                            [x for _, x in shares]) == secret

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
    #print(f'p={str(p)}')

    print_done(start)

    print_start('CRT sanity')
    start = timer()

    expected = (secret**2) % (np.prod(ms[:], dtype=np.int64))
    for i in range(len(shares)):
        share, mi = shares[i]
        shares[i] = ((share**2) % mi, mi)
    print(f'shares=' +
          str([f'{share % mi} (mod {mi})' for share, mi in shares]))
    actual = garner_algorithm([x for x, _ in shares], [x for _, x in shares])
    assert actual == expected, f'expected {expected}, actual={actual}'
    print_done(start)

    print_start('jobs assignment')
    start = timer()

    initial_state = 100
    processes = dict()
    result_q = multiprocessing.Queue(maxsize=k)
    for mod in ms[:k]:
        Mod.set_mod(mod)
        input_q = multiprocessing.JoinableQueue(maxsize=QUEUE_MAX_SIZE)
        process = multiprocessing.Process(target=worker,
                                          args=(
                                              p,
                                              mod,
                                              initial_state,
                                              input_q,
                                              result_q,
                                          ))
        processes[mod] = (process, input_q)
        process.start()

    print_done(start)

    print_start('file parsing')
    start = timer()

    line_length = 100
    total_lines = RANDOM_INPUT_LENGTH# // line_length
    for li in tqdm(range(total_lines)):
        random_char = random.choice(string.ascii_lowercase + '. \n')
        #inputs = list(map(encode, random_chars))
        for mod, (_, input_q) in processes.items():
            Mod.set_mod(mod)
            #for i in inputs:
            input_q.put(encode(random_char), block=True)

    for _, (_, input_q) in processes.items():
        input_q.put(None, block=True)  # send poison pill
    print_done(start)

    print_start('final results collection')
    start = timer()

    results = list()
    for mod, (proc, input_q) in processes.items():
        input_q.join()
        proc.join()
        results += [result_q.get(block=False)]

    next_state = garner_algorithm([x for x, _ in results],
                                  [x for _, x in results])
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
        states=[{
            'name': str(src),
            'tags': ['out: {:d}'.format(trans[1])]
        } for src, trans in transitions.items()],
        transitions=list(
            itertools.chain(*[[{
                'trigger': 'in: {:d}'.format(i),
                'source': str(src),
                'dest': str(t[0].get(i)),
                'after': str(t[1])
            } for i in t[0].keys()] for src, t in transitions.items()])),
        initial=str(200),
        show_state_attributes=True)
    fsm.get_graph().draw('diagram.png', prog='dot')

    print_done(start)


if __name__ == '__main__':
    main()
