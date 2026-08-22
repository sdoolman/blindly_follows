"""Lagrange polynomial interpolation and plotting utility."""

import sys
from collections.abc import Callable, Sequence

import matplotlib.pyplot as plt


def lagrange(
    points: Sequence[tuple[float | int, float | int]],
) -> Callable[[float], float]:
    """Return a callable polynomial function constructed using Lagrange interpolation."""
    n = len(points)

    def poly(x: float) -> float:
        total = 0.0
        for i in range(n):
            xi, yi = points[i]
            basis = 1.0
            for j in range(n):
                if i != j:
                    xj, _ = points[j]
                    basis *= (x - xj) / float(xi - xj)
            total += yi * basis
        return total

    return poly


def plot_interpolation(
    func: Callable[[float], float], points: Sequence[tuple[float | int, float | int]]
) -> None:
    """Plot the interpolated curve and sampled points."""
    x_vals = list(range(0, 100))
    y_vals = [func(x) for x in x_vals]

    plt.plot(x_vals, y_vals, linewidth=2.0, label="Lagrange Polynomial")
    x_pts = [p[0] for p in points]
    y_pts = [p[1] for p in points]
    plt.plot(x_pts, y_pts, "ro", label="Sample Points")
    plt.legend()
    plt.show()


def main() -> None:
    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        print("Usage: python lagrange.py <x1.y1> .. <x_k.y_k>")
        print("Example: python lagrange.py 0.1 2.4 4.5 3.2")
        return

    points = []
    for arg in sys.argv[1:]:
        parts = arg.split(".")
        if len(parts) == 2:
            points.append((int(parts[0]), int(parts[1])))

    poly_fn = lagrange(points)
    plot_interpolation(poly_fn, points)


if __name__ == "__main__":
    main()
