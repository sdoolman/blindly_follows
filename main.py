import random
from timeit import default_timer as timer

from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import add_state_features, Tags


###################################################################################################


def print_done(start_val):
    global elapsed
    elapsed = timer() - start_val
    print('< done, time elapsed: [{:.2f}] seconds'.format(elapsed))


def print_start(msg):
    print('> starting {:s}...'.format(msg))


def generate_data():
    states = range(1, 10)
    transitions = dict()
    for src in states:
        transitions[src] = (
            {0: random.choice(states), 1: random.choice(states)},
            random.randint(0, 1)
        )

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

    x_s, y_s = zip(*([(int('{:d}{:d}'.format(src, 0)),
                       int('{:d}{:d}'.format(t[0][0], t[1]))) for src, t in transitions.items()] +
                     [(int('{:d}{:d}'.format(src, 1)),
                       int('{:d}{:d}'.format(t[0][1], t[1]))) for src, t in transitions.items()]))

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
        transitions=[{'trigger': 'in: {:d}'.format(0),
                      'source': str(src),
                      'dest': str(trans[0][0]),
                      'after': str(trans[1])}
                     for src, trans in transitions.items()] +
                    [{'trigger': 'in: {:d}'.format(1),
                      'source': str(src),
                      'dest': str(trans[0][1]),
                      'after': str(trans[1])}
                     for src, trans in transitions.items()],
        initial=str(states[0]),
        show_state_attributes=True
    )
    m.get_graph().draw('diagram.png', prog='dot')

    elapsed = timer() - start
    print_done(start)

    start = timer()
