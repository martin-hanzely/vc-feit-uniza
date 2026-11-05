"""A shared, colorblind-checked color palette for matplotlib.

Quick start::

    import vc_feit_uniza
    vc_feit_uniza.use()          # light theme (or vc_feit_uniza.use("dark"))

    plt.plot(x, y)              # series colors come from the palette in fixed order
    plt.imshow(z, cmap="vc_seq")   # sequential (magnitude)
    plt.imshow(d, cmap="vc_div")   # diverging (above / below a midpoint)
"""

from __future__ import annotations

from typing import Literal

import matplotlib as mpl
from cycler import cycler
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

__all__ = [
    "CATEGORICAL",
    "SEQUENTIAL",
    "DIVERGING",
    "STATUS",
    "CHROME",
    "colors",
    "use",
    "register_cmaps",
]

Mode = Literal["light", "dark"]

# Categorical (identity). The ORDER is part of the design: adjacent slots were
# checked to stay distinguishable under common color-vision deficiencies.
# Always assign in this order; never generate a 9th color - fold into "Other".
CATEGORICAL: dict[Mode, dict[str, str]] = {
    "light": {
        "blue": "#2a78d6",
        "orange": "#eb6834",
        "aqua": "#1baf7a",
        "yellow": "#eda100",
        "magenta": "#e87ba4",
        "green": "#008300",
        "violet": "#6250d6",
        "red": "#e34948",
    },
    "dark": {
        "blue": "#3987e5",
        "orange": "#d95926",
        "aqua": "#199e70",
        "yellow": "#c98500",
        "magenta": "#d55181",
        "green": "#008300",
        "violet": "#9085e9",
        "red": "#e66767",
    },
}

# Sequential (magnitude): one hue, light -> dark.
SEQUENTIAL: dict[int, str] = {
    100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef",
    300: "#6da7ec", 350: "#5598e7", 400: "#3987e5", 450: "#2a78d6",
    500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281",
    700: "#0d366b",
}

# Diverging (polarity): blue <-> red with a neutral gray midpoint.
DIVERGING: dict[Mode, list[str]] = {
    "light": ["#0d366b", "#2a78d6", "#9ec5f4", "#f0efec", "#f2a3a2", "#e34948", "#8a1f1f"],
    "dark": ["#9ec5f4", "#3987e5", "#184f95", "#383835", "#a33a3a", "#e66767", "#f5b3b2"],
}

# Status colors are reserved for state. Never use them as "series 4".
# Always pair them with an icon or text label, never color alone.
STATUS: dict[str, str] = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

# Surfaces, ink, and axes.
CHROME: dict[Mode, dict[str, str]] = {
    "light": {
        "surface": "#fcfcfb",
        "text": "#0b0b0b",
        "text_secondary": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
    },
    "dark": {
        "surface": "#1a1a19",
        "text": "#f0efec",
        "text_secondary": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
    },
}


def colors(mode: Mode = "light") -> list[str]:
    """The 8 categorical colors in their fixed order."""
    return list(CATEGORICAL[mode].values())


def register_cmaps(mode: Mode = "light") -> None:
    """Register `vc_seq`, `vc_div`, `vc_cat` (+ `_r` versions) with matplotlib."""
    seq = [SEQUENTIAL[k] for k in sorted(SEQUENTIAL)]
    if mode == "dark":
        seq = seq[::-1]  # on dark, "more" reads as brighter
    maps = [
        LinearSegmentedColormap.from_list("vc_seq", seq),
        LinearSegmentedColormap.from_list("vc_div", DIVERGING[mode]),
        ListedColormap(colors(mode), name="vc_cat"),
    ]
    for cmap in maps:
        for c in (cmap, cmap.reversed()):
            mpl.colormaps.register(c, force=True)


def use(mode: Mode = "light") -> None:
    """Apply the palette and a quiet chart style to matplotlib's global settings."""
    if mode not in CHROME:
        raise ValueError(f"mode must be 'light' or 'dark', got {mode!r}")
    c = CHROME[mode]
    register_cmaps(mode)
    mpl.rcParams.update(
        {
            "axes.prop_cycle": cycler(color=colors(mode)),
            "image.cmap": "vc_seq",
            # surfaces
            "figure.facecolor": c["surface"],
            "axes.facecolor": c["surface"],
            "savefig.facecolor": c["surface"],
            # ink
            "text.color": c["text"],
            "axes.labelcolor": c["text_secondary"],
            "axes.titlecolor": c["text"],
            "xtick.color": c["muted"],
            "ytick.color": c["muted"],
            "xtick.labelcolor": c["text_secondary"],
            "ytick.labelcolor": c["text_secondary"],
            "legend.labelcolor": c["text_secondary"],
            # recessive axes and grid
            "axes.edgecolor": c["axis"],
            "axes.linewidth": 1.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "grid.color": c["grid"],
            "grid.linewidth": 1.0,
            "grid.linestyle": "-",
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            # marks
            "lines.linewidth": 2.0,
            "lines.solid_capstyle": "round",
            "lines.solid_joinstyle": "round",
            "lines.markersize": 8,
            "lines.markeredgewidth": 2,
            "lines.markeredgecolor": c["surface"],
            "scatter.edgecolors": c["surface"],
            "patch.edgecolor": c["surface"],
            "patch.linewidth": 0,
            # type
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.titlepad": 12,
            "legend.frameon": False,
            "figure.dpi": 110,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
        }
    )
