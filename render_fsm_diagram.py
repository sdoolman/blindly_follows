"""Generate visual diagram for the DUFSM state machine."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt

def generate_fsm_diagram(output_file: str = "diagram.png") -> None:
    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    ax.set_xlim(-1, 11)
    ax.set_ylim(-1.5, 3.5)
    ax.axis("off")

    # States definition
    states = {
        "200": (0.0, 1.0, "State 200\n[out: 0] (init)"),
        "400": (2.5, 1.0, "State 400\n[out: 0] ('n')"),
        "600": (5.0, 1.0, "State 600\n[out: 0] ('na')"),
        "800": (7.5, 1.0, "State 800\n[out: 0] ('nan')"),
        "900": (10.0, 1.0, "State 900\n[out: 1] ('nano' MATCH)"),
    }

    # Draw state nodes
    for s, (x, y, label) in states.items():
        color = "#2E7D32" if s == "900" else "#1565C0"
        circle = plt.Circle((x, y), 0.55, color=color, ec="#111111", lw=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, s, ha="center", va="center", color="white", fontweight="bold", fontsize=11, zorder=4)
        ax.text(x, y - 0.85, label, ha="center", va="top", fontsize=8.5, color="#222222", fontweight="medium")

    def draw_arrow(x1: float, y1: float, x2: float, y2: float, label: str, curve: float = 0.0, label_offset: tuple[float, float] = (0, 0)) -> None:
        style = f"arc3,rad={curve}"
        arrow = patches.FancyArrowPatch(
            (x1, y1), (x2, y2),
            connectionstyle=style,
            arrowstyle="->,head_length=6,head_width=4",
            color="#444444", lw=1.5, zorder=2
        )
        ax.add_patch(arrow)
        mid_x = (x1 + x2) / 2 + label_offset[0]
        mid_y = (y1 + y2) / 2 + curve * 1.2 + label_offset[1]
        ax.text(
            mid_x, mid_y, label, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#0D47A1",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#BBDEFB", alpha=0.9), zorder=5
        )

    # Forward transitions ('nano')
    draw_arrow(0.55, 1.1, 1.95, 1.1, "in: 'n'", curve=0.15)
    draw_arrow(3.05, 1.1, 4.45, 1.1, "in: 'a'", curve=0.15)
    draw_arrow(5.55, 1.1, 6.95, 1.1, "in: 'n'", curve=0.15)
    draw_arrow(8.05, 1.1, 9.45, 1.1, "in: 'o'", curve=0.15)

    # Fallback transitions
    draw_arrow(4.7, 0.6, 2.8, 0.6, "in: 'n'", curve=-0.25)
    draw_arrow(7.2, 0.5, 2.7, 0.4, "in: 'n'", curve=-0.35)
    draw_arrow(7.3, 0.6, 5.2, 0.6, "in: 'a'", curve=-0.25)

    ax.text(
        5.0, 2.9,
        "Distributed Unknown Finite State Machine (DUFSM)\nPattern 'nano' Detector over Blind CRT Polynomial Shares",
        ha="center", va="center", fontsize=12, fontweight="bold", color="#111111"
    )

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Generated {output_file} successfully.")

if __name__ == "__main__":
    generate_fsm_diagram("diagram.png")
