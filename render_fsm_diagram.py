"""Generate high-contrast, publication-quality state machine diagram for README."""

import io
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

# DOT definition with clean, publication-grade styling and solid white background
DOT_GRAPH = """
digraph "DUFSM_State_Machine" {
    graph [
        bgcolor="#FFFFFF"
        rankdir=LR
        nodesep=0.8
        ranksep=1.0
        fontsize=13
        fontname="Helvetica-Bold"
        label="Distributed Unknown Finite State Machine (DUFSM) - 'nano' Pattern Detector\\n"
        labelloc="t"
        pad="0.5"
    ]
    node [
        fontname="Helvetica"
        fontsize=11
        shape=rectangle
        style="rounded,filled"
        color="#263238"
        penwidth=1.5
        margin="0.2,0.1"
    ]
    edge [
        fontname="Helvetica"
        fontsize=10
        color="#37474F"
        penwidth=1.5
        arrowsize=0.8
    ]

    // States definition
    s200 [label="State 200\\n[out: 0]\\n(Initial)", fillcolor="#E3F2FD", color="#1565C0"]
    s400 [label="State 400\\n[out: 0]\\n('n')", fillcolor="#FFF3E0", color="#E65100", peripheries=2]
    s600 [label="State 600\\n[out: 0]\\n('na')", fillcolor="#FFF3E0", color="#E65100"]
    s800 [label="State 800\\n[out: 0]\\n('nan')", fillcolor="#FFF3E0", color="#E65100"]
    s900 [label="State 900\\n[out: 1]\\n(MATCH)", fillcolor="#E8F5E9", color="#2E7D32", penwidth=2]

    // Forward 'nano' sequence transitions (highlighted green/bold)
    s200 -> s400 [label="in: 'n' (28)", color="#2E7D32", fontcolor="#1B5E20", penwidth=2.2]
    s400 -> s600 [label="in: 'a' (2)", color="#2E7D32", fontcolor="#1B5E20", penwidth=2.2]
    s600 -> s800 [label="in: 'n' (28)", color="#2E7D32", fontcolor="#1B5E20", penwidth=2.2]
    s800 -> s900 [label="in: 'o' (30) [MATCH]", color="#2E7D32", fontcolor="#1B5E20", penwidth=2.5]

    // Partial match & rollback transitions
    s400 -> s400 [label="in: 'n' (28)", color="#E65100", fontcolor="#BF360C"]
    s800 -> s400 [label="in: 'n' (28)", color="#E65100", fontcolor="#BF360C"]
    s800 -> s600 [label="in: 'a' (2)", color="#E65100", fontcolor="#BF360C"]

    // Default / reset transitions
    s200 -> s200 [label="in: other\\n(2..58)", style=dashed, color="#78909C", fontcolor="#546E7A"]
    s400 -> s200 [label="in: other", style=dashed, color="#78909C", fontcolor="#546E7A"]
    s600 -> s200 [label="in: other", style=dashed, color="#78909C", fontcolor="#546E7A"]
    s800 -> s200 [label="in: other", style=dashed, color="#78909C", fontcolor="#546E7A"]
    s900 -> s900 [label="in: any (terminal)\\n(2..58)", color="#2E7D32", fontcolor="#1B5E20"]
}
"""


def generate_fsm_diagram(output_file: Path | str = "diagram.png") -> None:
    """Generate high-resolution PNG diagram with solid white background."""
    target_path = Path(output_file)

    url = "https://quickchart.io/graphviz?format=png&graph=" + urllib.parse.quote(DOT_GRAPH)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        raw_bytes = r.read()

    im = Image.open(io.BytesIO(raw_bytes))
    # Ensure solid white background and RGB mode for dark/light mode compatibility
    bg = Image.new("RGB", im.size, (255, 255, 255))
    if im.mode in ("RGBA", "LA"):
        bg.paste(im, mask=im.split()[-1])
    else:
        bg.paste(im)

    bg.save(target_path, format="PNG", optimize=True)
    w, h = bg.size
    size_b = target_path.stat().st_size
    print(f"Generated publication-grade {target_path} ({w}x{h} RGB PNG, {size_b} bytes).")


if __name__ == "__main__":
    generate_fsm_diagram("diagram.png")
