"""Generate exact original GraphMachine Graphviz visual diagram for the state machine."""

import itertools
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from transitions.extensions import GraphMachine as Machine
from transitions.extensions.states import Tags, add_state_features

from main import generate_data


def generate_fsm_diagram(output_file: Path | str = "diagram.png") -> None:
    """Generate exact GraphMachine Graphviz state diagram."""
    target_path = Path(output_file)
    transitions = generate_data()

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
    graph = fsm.get_graph()
    dot_source = graph.source

    # Try local dot CLI first if installed
    try:
        subprocess.run(
            ["dot", "-Tpng", "-o", str(target_path)],
            input=dot_source.encode("utf-8"),
            capture_output=True,
            check=True,
        )
        print(f"Rendered {target_path} via local Graphviz dot.")
        return
    except Exception:
        pass

    # Fallback to Graphviz engine API (explicit PNG format)
    url = "https://quickchart.io/graphviz?format=png&graph=" + urllib.parse.quote(dot_source)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        img_bytes = r.read()
        target_path.write_bytes(img_bytes)
        print(f"Rendered exact GraphMachine Graphviz {target_path} ({len(img_bytes)} bytes).")


if __name__ == "__main__":
    generate_fsm_diagram("diagram.png")
