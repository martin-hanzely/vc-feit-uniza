"""Render the example charts used in the README (light + dark versions).

    uv run python examples/make_examples.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import team_palette as tp

OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
rng = np.random.default_rng(7)


def swatches(mode):
    cat = tp.CATEGORICAL[mode]
    c = tp.CHROME[mode]
    fig, axes = plt.subplots(3, 1, figsize=(9, 4.2), height_ratios=[1.3, 0.6, 0.6])
    for ax in axes:
        ax.set_axis_off()

    ax = axes[0]
    ax.set_title("Categorical (use in this order)", loc="left")
    for i, (name, hexv) in enumerate(cat.items()):
        ax.add_patch(plt.Rectangle((i, 0.35), 0.9, 0.65, color=hexv, lw=0))
        ax.text(i, 0.18, f"{i + 1}  {name}", fontsize=9, color=c["text"])
        ax.text(i, 0.0, hexv, fontsize=8, color=c["text_secondary"], family="monospace")
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 1)

    grad = np.linspace(0, 1, 256)[None, :]
    for ax, cmap, title in (
        (axes[1], "team_seq", "Sequential: team_seq"),
        (axes[2], "team_div", "Diverging: team_div"),
    ):
        ax.set_axis_on()
        ax.imshow(grad, aspect="auto", cmap=cmap)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(title, loc="left", fontsize=10)
    fig.tight_layout()
    return fig


def line(mode):
    c = tp.CHROME[mode]
    months = np.arange(1, 13)
    names = ["Bratislava", "Vienna", "Prague", "Budapest"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ends = []
    for i, name in enumerate(names):
        y = 40 + 12 * i + np.cumsum(rng.normal(1.5, 4, 12))
        (ln,) = ax.plot(months, y, label=name)
        ax.plot(months[-1], y[-1], "o", color=ln.get_color())
        ends.append([y[-1], name])
    # direct labels at line ends, nudged apart so they never overlap
    ends.sort()
    for a, b in zip(ends, ends[1:]):
        b[0] = max(b[0], a[0] + 4)
    for y_lab, name in ends:
        ax.annotate(name, (months[-1], y_lab), xytext=(10, 0), textcoords="offset points",
                    va="center", fontsize=9, color=c["text_secondary"])
    ax.set_title("Monthly bookings by city")
    ax.set_xticks(months, ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.set_ylabel("Bookings")
    ax.set_xlim(0.6, 13.6)
    ax.legend(loc="upper left", ncols=4, bbox_to_anchor=(0, -0.08))
    return fig


def bars(mode):
    c = tp.CHROME[mode]
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    series = {"Flights": [42, 55, 61, 48], "Hotels": [30, 38, 52, 35], "Tours": [12, 20, 31, 18]}
    x = np.arange(len(quarters))
    w = 0.22
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for i, (name, vals) in enumerate(series.items()):
        ax.bar(x + (i - 1) * (w + 0.02), vals, w, label=name)
    ax.set_xticks(x, quarters)
    ax.set_title("Revenue by product (k€)")
    ax.legend(loc="lower right", ncols=3, bbox_to_anchor=(1, 1))
    ax.spines["left"].set_visible(False)
    ax.axhline(0, color=c["axis"], lw=1)
    return fig


def stacked(mode):
    c = tp.CHROME[mode]
    regions = ["North", "South", "East", "West", "Central"]
    parts = {"Online": [50, 42, 38, 61, 45], "Agency": [28, 35, 30, 18, 25], "Phone": [10, 12, 18, 9, 14]}
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bottom = np.zeros(len(regions))
    for name, vals in parts.items():
        # 2px surface-colored edge = the gap between stacked segments
        ax.barh(regions, vals, left=bottom, height=0.5, label=name,
                edgecolor=c["surface"], linewidth=2)
        bottom += vals
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.spines["left"].set_visible(False)
    ax.set_title("Bookings by channel and region")
    ax.legend(loc="lower right", ncols=3, bbox_to_anchor=(1, 1))
    return fig


def scatter(mode):
    # Scatter shows every color next to every other -> keep to 3 series.
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for name, (mx, my) in {"Weekend": (3, 220), "City break": (5, 420), "Long-haul": (11, 1150)}.items():
        x = rng.normal(mx, 1.2, 40).clip(1)
        y = rng.normal(my, my * 0.18, 40)
        ax.scatter(x, y, s=45, linewidths=1.5, label=name)
    ax.set_xlabel("Trip length (days)")
    ax.set_ylabel("Price (€)")
    ax.set_title("Price vs trip length")
    ax.grid(True, axis="both")
    ax.legend(loc="upper left")
    return fig


def heatmaps(mode):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = np.arange(0, 24, 3)

    occ = rng.gamma(2, 1, (7, len(hours))) + np.linspace(0, 3, 7)[:, None]
    im1 = a1.imshow(occ, cmap="team_seq", aspect="auto")
    a1.set_title("Sequential: search volume")
    fig.colorbar(im1, ax=a1, shrink=0.8).outline.set_visible(False)

    diff = rng.normal(0, 1, (7, len(hours))).cumsum(axis=1) / 2
    lim = np.abs(diff).max()
    im2 = a2.imshow(diff, cmap="team_div", vmin=-lim, vmax=lim, aspect="auto")
    a2.set_title("Diverging: change vs last year")
    fig.colorbar(im2, ax=a2, shrink=0.8).outline.set_visible(False)

    for ax in (a1, a2):
        ax.set_yticks(range(7), days)
        ax.set_xticks(range(len(hours)), [f"{h:02d}h" for h in hours])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.tight_layout()
    return fig


CHARTS = {
    "palette": swatches,
    "line": line,
    "bars": bars,
    "stacked": stacked,
    "scatter": scatter,
    "heatmaps": heatmaps,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for mode in ("light", "dark"):
        tp.use(mode)
        for name, fn in CHARTS.items():
            fig = fn(mode)
            path = OUT / f"{name}-{mode}.png"
            fig.savefig(path)
            plt.close(fig)
            print("wrote", path.relative_to(OUT.parent.parent))


if __name__ == "__main__":
    main()
