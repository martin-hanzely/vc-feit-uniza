"""Render the example charts used in the README (light + dark versions).

The data is synthetic but shaped like our real work: IMU recordings,
model training, and image-classification results.

    uv run python examples/make_examples.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.ticker import PercentFormatter

import team_palette as tp

OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
FS = 100  # IMU sample rate (Hz)


def ink_for(color):
    """Readable text color on top of a filled cell."""
    r, g, b = to_rgb(color)
    light_bg = 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.5
    return tp.CHROME["light"]["text"] if light_bg else tp.CHROME["dark"]["text"]


def end_labels(ax, x, ys, names, mode, gap):
    """Label each line at its right end, nudged apart so labels never overlap."""
    ends = sorted([y[-1], n] for y, n in zip(ys, names))
    for a, b in zip(ends, ends[1:]):
        b[0] = max(b[0], a[0] + gap)
    for y, n in ends:
        ax.annotate(n, (x[-1], y), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=9, color=tp.CHROME[mode]["text_secondary"])


def hide_frame(ax):
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)


def imu_signal(seed=1):
    """15 s of wrist IMU: standing, walking, then running."""
    rng = np.random.default_rng(seed)
    t = np.arange(0, 15, 1 / FS)
    step = np.where(t < 4, 0, np.where(t < 10, 1.8, 2.8))  # step frequency (Hz)
    amp = np.where(t < 4, 0.05, np.where(t < 10, 1.0, 2.4))
    phase = 2 * np.pi * np.cumsum(step) / FS
    acc = np.stack([
        amp * 2.0 * np.sin(phase) + rng.normal(0, 0.15, t.size),
        amp * 1.2 * np.sin(2 * phase + 0.6) + rng.normal(0, 0.15, t.size),
        9.81 + amp * 3.0 * np.abs(np.sin(phase)) + rng.normal(0, 0.15, t.size),
    ])
    gyro = np.stack([
        amp * 1.5 * np.cos(phase) + rng.normal(0, 0.05, t.size),
        amp * 0.8 * np.sin(phase + 1.2) + rng.normal(0, 0.05, t.size),
        amp * 0.4 * np.sin(2 * phase) + rng.normal(0, 0.05, t.size),
    ])
    return t, acc, gyro


# ---------------------------------------------------------------- charts


def palette(mode):
    cat = tp.CATEGORICAL[mode]
    c = tp.CHROME[mode]
    fig, axes = plt.subplots(3, 1, figsize=(9, 4.2), height_ratios=[1.3, 0.6, 0.6])
    ax = axes[0]
    ax.set_axis_off()
    ax.set_title("Categorical (use in this order)")
    for i, (name, hexv) in enumerate(cat.items()):
        ax.add_patch(plt.Rectangle((i, 0.35), 0.9, 0.65, color=hexv, lw=0))
        ax.text(i, 0.18, f"{i + 1}  {name}", fontsize=9, color=c["text"])
        ax.text(i, 0.0, hexv, fontsize=8, color=c["text_secondary"], family="monospace")
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 1)
    grad = np.linspace(0, 1, 256)[None, :]
    for ax, cmap, title in ((axes[1], "team_seq", "Sequential: team_seq"),
                            (axes[2], "team_div", "Diverging: team_div")):
        ax.imshow(grad, aspect="auto", cmap=cmap)
        ax.set_xticks([])
        ax.set_yticks([])
        hide_frame(ax)
        ax.set_title(title, fontsize=10)
    fig.tight_layout()
    return fig


def imu(mode):
    """Accelerometer and gyroscope as two panels on a shared time axis (never a dual y-axis)."""
    t, acc, gyro = imu_signal()
    c = tp.CHROME[mode]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 5.4), sharex=True)
    names = ["x", "y", "z"]
    for ax, data, unit, title in ((a1, acc, "m/s²", "Accelerometer"),
                                  (a2, gyro, "rad/s", "Gyroscope")):
        ax.set_ylabel(f"{title}\n({unit})")
        for d, n in zip(data, names):
            ax.plot(t, d, lw=1.2, label=f"{n} axis")  # thinner than 2px: dense 100 Hz signal
        end_labels(ax, t, data, names, mode, gap=(data.max() - data.min()) * 0.09)
    for x0, x1, name in ((0, 4, "standing"), (4, 10, "walking"), (10, 15, "running")):
        a1.text((x0 + x1) / 2, 1.04, name, transform=a1.get_xaxis_transform(),
                ha="center", fontsize=9, color=c["text_secondary"])
        if x0:
            for ax in (a1, a2):
                ax.axvline(x0, color=c["axis"], lw=1)
    a2.set_xlabel("Time (s)")
    a2.set_xlim(0, 15.8)
    a2.legend(loc="upper left", ncols=3, bbox_to_anchor=(0, -0.28))
    fig.suptitle("Wrist IMU recording", x=0.012, ha="left", fontweight="semibold")
    fig.tight_layout()
    return fig


def spectrogram(mode):
    t, acc, _ = imu_signal()
    mag = np.linalg.norm(acc, axis=0)
    mag -= mag.mean()
    fig, ax = plt.subplots(figsize=(9, 3.8))
    _, _, _, im = ax.specgram(mag, Fs=FS, NFFT=256, noverlap=224, cmap="team_seq",
                              scale="dB", vmin=-35)
    ax.set_ylim(0, 12)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title("Spectrogram of acceleration magnitude")
    hide_frame(ax)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.outline.set_visible(False)
    cb.set_label("Power (dB)")
    return fig


def training(mode):
    """Loss and accuracy as small multiples; train = slot 1, validation = slot 2 in both."""
    rng = np.random.default_rng(3)
    ep = np.arange(1, 51)
    over = np.clip(ep - 22, 0, None)
    train_loss = 2.2 * np.exp(-ep / 9) + 0.08 + rng.normal(0, 0.02, ep.size)
    val_loss = 2.1 * np.exp(-ep / 10) + 0.25 + 0.006 * over**1.3 + rng.normal(0, 0.03, ep.size)
    train_acc = 0.99 - 0.85 * np.exp(-ep / 8) + rng.normal(0, 0.005, ep.size)
    val_acc = 0.91 - 0.85 * np.exp(-ep / 9) - 0.0008 * over**1.2 + rng.normal(0, 0.008, ep.size)
    best = ep[np.argmin(val_loss)]
    c = tp.CHROME[mode]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    for ax, tr, va, title in ((a1, train_loss, val_loss, "Loss"),
                              (a2, train_acc, val_acc, "Accuracy")):
        ax.plot(ep, tr, label="train")
        ax.plot(ep, va, label="validation")
        ax.axvline(best, color=c["muted"], lw=1)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Epoch")
        ax.set_xlim(0, 60)
        span = max(tr.max(), va.max()) - min(tr.min(), va.min())
        end_labels(ax, ep, [tr, va], ["train", "validation"], mode, gap=span * 0.07)
    a1.annotate(f"best checkpoint\n(epoch {best})", (best, 1), xycoords=("data", "axes fraction"),
                xytext=(6, -4), textcoords="offset points", va="top", fontsize=9,
                color=c["text_secondary"])
    a2.yaxis.set_major_formatter(PercentFormatter(1.0))
    a2.legend(loc="lower right", bbox_to_anchor=(1, 1.08), ncols=2)
    fig.suptitle("Training a 6-class image classifier (ResNet-18)",
                 x=0.012, ha="left", fontweight="semibold")
    fig.tight_layout()
    return fig


CLASSES = ["cell", "debris", "bubble", "crystal", "fiber", "cluster"]


def confusion(mode):
    rng = np.random.default_rng(5)
    n = len(CLASSES)
    cm = rng.integers(0, 12, (n, n)).astype(float)
    np.fill_diagonal(cm, rng.integers(150, 240, n))
    cm[0, 5] += 45  # cells get mistaken for clusters
    cm[1, 4] += 30  # debris vs fiber
    cmn = cm / cm.sum(axis=1, keepdims=True)
    cmap = plt.get_cmap("team_seq")
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(cmn, cmap=cmap, vmin=0, vmax=1)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{cmn[i, j]:.2f}", ha="center", va="center", fontsize=9,
                    color=ink_for(cmap(cmn[i, j])))
    ax.set_xticks(range(n), CLASSES, rotation=30, ha="right")
    ax.set_yticks(range(n), CLASSES)
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("True class")
    ax.set_title("Confusion matrix (row-normalized)")
    hide_frame(ax)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.outline.set_visible(False)
    return fig


def metrics(mode):
    rng = np.random.default_rng(6)
    p = rng.uniform(0.78, 0.97, len(CLASSES))
    r = rng.uniform(0.70, 0.96, len(CLASSES))
    vals = {"precision": p, "recall": r, "F1": 2 * p * r / (p + r)}
    x = np.arange(len(CLASSES))
    w = 0.24
    fig, ax = plt.subplots(figsize=(9, 4))
    for i, (name, v) in enumerate(vals.items()):
        ax.bar(x + (i - 1) * (w + 0.02), v, w, label=name)
    ax.set_xticks(x, CLASSES)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.spines["left"].set_visible(False)
    ax.set_title("Per-class metrics on the test set")
    ax.legend(loc="lower right", ncols=3, bbox_to_anchor=(1, 1))
    return fig


def embedding(mode):
    """2-D embedding (e.g. UMAP of CNN features). Scatter: max 3 colored classes, rest in gray."""
    rng = np.random.default_rng(8)
    c = tp.CHROME[mode]
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    others = [(4, -3), (1, 0), (5, 2)]
    pts = np.concatenate([rng.normal(o, 0.9, (90, 2)) for o in others])
    ax.scatter(*pts.T, s=18, color=c["axis"], linewidths=0, label="other classes")
    for name, ctr in {"cell": (-4, 1), "debris": (2, 4), "cluster": (-2, -1.5)}.items():
        p = rng.normal(ctr, [1.0, 0.8], (120, 2))
        ax.scatter(*p.T, s=26, linewidths=1, label=name)
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_title("Feature embedding of test images")
    # legend order: colored classes first, gray "other" last
    h, lab = ax.get_legend_handles_labels()
    ax.legend(h[1:] + h[:1], lab[1:] + lab[:1], loc="upper left", bbox_to_anchor=(1, 1))
    return fig


def correlation(mode):
    t, acc, gyro = imu_signal(seed=2)
    rng = np.random.default_rng(9)
    mag = 0.6 * acc[0] - 0.8 * gyro[0] + rng.normal(0, 1, t.size)
    data = np.vstack([acc, gyro, mag])
    names = ["acc x", "acc y", "acc z", "gyro x", "gyro y", "gyro z", "mag x"]
    corr = np.corrcoef(data)
    cmap = plt.get_cmap("team_div")
    fig, ax = plt.subplots(figsize=(6.6, 5.4))
    im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1)
    for i in range(len(names)):
        for j in range(len(names)):
            label = f"{corr[i, j]:+.2f}".replace("-0.00", "0.00").replace("+0.00", "0.00")
            ax.text(j, i, label, ha="center", va="center", fontsize=8,
                    color=ink_for(cmap((corr[i, j] + 1) / 2)))
    ax.set_xticks(range(len(names)), names, rotation=30, ha="right")
    ax.set_yticks(range(len(names)), names)
    ax.set_title("Correlation between IMU channels")
    hide_frame(ax)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.outline.set_visible(False)
    return fig


CHARTS = {
    "palette": palette,
    "imu": imu,
    "spectrogram": spectrogram,
    "training": training,
    "confusion": confusion,
    "metrics": metrics,
    "embedding": embedding,
    "correlation": correlation,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
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
