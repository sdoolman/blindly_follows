"""Main simulation: Blind FSM evaluation over CRT secret shares and polynomial interpolation."""

import itertools
import math
import multiprocessing
import pickle
import random
import string
from pathlib import Path
from timeit import default_timer as timer

import matplotlib
from tqdm import tqdm
from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import Tags, add_state_features

from crt.generic_functions import get_mignotte_params
from polynomials.polymod import Mod, PolyMod
from secret_sharing.mathlib import garner_algorithm

matplotlib.use("Agg")

RANDOM_INPUT_LENGTH: int = 2**15
QUEUE_MAX_SIZE: int = 100

SPECIAL_ENCODINGS: dict[str, int] = {
    ".": 27,
    " ": 28,
    "\n": 29,
}


def print_done(start_val: float) -> None:
    elapsed = timer() - start_val
    print(f"< done! time elapsed: [{elapsed:.2f}] seconds")


def print_start(msg: str) -> None:
    print(f"> starting {msg}...")


def encode(character: str) -> int:
    """Encode character into a unique even integer identifier."""
    if character in SPECIAL_ENCODINGS:
        code = SPECIAL_ENCODINGS[character]
    elif character in string.ascii_letters:
        code = ord(character.lower()) - ord("`")
    else:
        raise ValueError(
            f"Failed to encode character [{character}] - consider adding support for it"
        )
    return code * 2


def generate_data() -> dict[int, tuple[dict[int, int], int]]:
    """Generate state machine transition mapping and binary output tags."""
    data = {k: ({}, random.randint(0, 1)) for k in {200, 400, 600, 800, 900}}
    charset = string.ascii_lowercase + ". \n"

    for state in (200, 400, 600, 800):
        data[state][0].update({encode(c): 200 for c in charset})
    data[900][0].update({encode(c): 900 for c in charset})

    data[200][0].update({encode("n"): 400})
    data[400][0].update({encode("n"): 400, encode("a"): 600})
    data[600][0].update({encode("n"): 800})
    data[800][0].update({encode("o"): 900, encode("n"): 400, encode("a"): 600})

    return data


def worker(
    poly: PolyMod,
    mod: int,
    current_state: int,
    input_q: multiprocessing.JoinableQueue,
    results_q: multiprocessing.Queue,
) -> None:
    """Worker process evaluating modular polynomial blindly for modulus `mod`."""
    Mod.set_mod(mod)
    next_state = current_state
    while True:
        item = input_q.get(block=True)
        if item is None:
            input_q.task_done()
            break
        next_state = poly(next_state + item).value
        input_q.task_done()

    results_q.put_nowait((next_state, mod))


def get_or_create_polynomial(
    xy_s: dict[int, int], ms: list[int], cache_path: Path | str = "polynomial.json"
) -> PolyMod:
    """Load cached modular polynomial or interpolate from scratch."""
    path = Path(cache_path)
    legacy_bin = path.with_name("p.bin")

    Mod.set_mod(math.prod(ms))
    if path.exists():
        return PolyMod.load_json(path)
    if legacy_bin.exists():
        with legacy_bin.open("rb") as f:
            poly = pickle.load(f)
        poly.save_json(path)
        return poly

    poly = PolyMod.interpolate(list(xy_s.items()))
    poly.save_json(path)
    return poly


def render_diagram(
    transitions: dict[int, tuple[dict[int, int], int]],
    output_path: Path | str = "diagram.png",
) -> None:
    """Render state machine diagram to PNG using Graphviz."""

    @add_state_features(Tags)
    class CustomStateMachine(Machine):
        pass

    class Matter:
        pass

    lump = Matter()
    states_def = [
        {"name": str(src), "tags": [f"out: {trans[1]}"]} for src, trans in transitions.items()
    ]
    transitions_def = list(
        itertools.chain(
            *[
                [
                    {
                        "trigger": f"in: {i}",
                        "source": str(src),
                        "dest": str(t[0].get(i)),
                        "after": str(t[1]),
                    }
                    for i in t[0]
                ]
                for src, t in transitions.items()
            ]
        )
    )

    fsm = CustomStateMachine(
        model=lump,
        states=states_def,
        transitions=transitions_def,
        initial=str(400),
        show_state_attributes=True,
    )
    target = Path(output_path)
    try:
        fsm.get_graph().draw(str(target), prog="dot")
    except Exception:
        import urllib.parse
        import urllib.request
        dot_source = fsm.get_graph().source
        url = "https://quickchart.io/graphviz?graph=" + urllib.parse.quote(dot_source)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r:
            target.write_bytes(r.read())


def main() -> None:
    print_start("state machine data generation")
    start = timer()
    transitions = generate_data()

    xy_s = {
        x: y
        for (x, y) in itertools.chain.from_iterable(
            [(src + i, t[0].get(i)) for i in t[0]] for src, t in transitions.items()
        )
    }
    print_done(start)

    print_start("mignotte parameters calculation")
    start = timer()
    n, k = 5, 5
    authorized_range, ms = get_mignotte_params(xy_s, n=n, k=k)
    secret = random.choice(authorized_range)
    shares = [(secret % mi, mi) for mi in ms[:k]]
    print("shares=" + str([f"{share} (mod {mi})" for share, mi in shares]))
    assert garner_algorithm([x for x, _ in shares], [x for _, x in shares]) == secret
    print_done(start)

    print_start("polynomial interpolation")
    Mod.set_mod(math.prod(ms))
    p = get_or_create_polynomial(xy_s, ms)
    print_done(start)

    print_start("CRT sanity")
    start = timer()
    expected = (secret**2) % math.prod(ms)
    shares_sq = [((share**2) % mi, mi) for share, mi in shares]
    print("shares^2=" + str([f"{s % mi} (mod {mi})" for s, mi in shares_sq]))
    actual = garner_algorithm([x for x, _ in shares_sq], [x for _, x in shares_sq])
    assert actual == expected, f"expected {expected}, actual={actual}"
    print_done(start)

    print_start("jobs assignment")
    start = timer()
    initial_state = 200
    processes: dict[int, tuple[multiprocessing.Process, multiprocessing.JoinableQueue]] = {}
    result_q: multiprocessing.Queue = multiprocessing.Queue(maxsize=k)

    for mod in ms[:k]:
        Mod.set_mod(mod)
        input_q = multiprocessing.JoinableQueue(maxsize=QUEUE_MAX_SIZE)
        process = multiprocessing.Process(
            target=worker,
            args=(p, mod, initial_state, input_q, result_q),
        )
        processes[mod] = (process, input_q)
        process.start()
    print_done(start)

    print_start("file parsing")
    start = timer()
    for _ in tqdm(range(RANDOM_INPUT_LENGTH)):
        random_char = random.choice(string.ascii_lowercase + ". \n")
        encoded_val = encode(random_char)
        for mod, (_, input_q) in processes.items():
            Mod.set_mod(mod)
            input_q.put(encoded_val, block=True)

    for _, input_q in processes.values():
        input_q.put(None, block=True)
    print_done(start)

    print_start("final results collection")
    start = timer()
    results = []
    for proc, input_q in processes.values():
        input_q.join()
        proc.join()
        results.append(result_q.get(block=False))

    next_state = garner_algorithm([x for x, _ in results], [x for _, x in results])
    print(f"next state is: [{next_state}]!")
    print_done(start)

    print_start("state machine drawing")
    start = timer()
    try:
        render_diagram(transitions, "diagram.png")
    except Exception as e:
        print(f"Note: Graphviz dot render skipped or failed: {e}")
    print_done(start)


if __name__ == "__main__":
    main()
