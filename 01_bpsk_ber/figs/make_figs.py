# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy", "matplotlib"]
# ///
"""產生 HACKMD.md 用的教學圖，輸出到本檔所在的 figs/ 資料夾。

用法：uv run figs/make_figs.py     （在 01_bpsk_ber/ 內執行）

圖表規範：白底、Times New Roman（本機沒有時用 Liberation Serif）、只用黑白灰與線型、網底區分，
灰階列印也能辨識。圖內文字用英文，避免字型缺中文字。
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erfc
from scipy.stats import norm

OUT = Path(__file__).resolve().parent

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "axes.labelsize": 16, "axes.titlesize": 16, "legend.fontsize": 12,
    "xtick.labelsize": 13, "ytick.labelsize": 13,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "hatch.linewidth": 0.8,
})


def sigma_of(ebn0_db: float) -> float:
    """Eb = 1 時的雜訊標準差，對應 HACKMD.md 式 (4)。"""
    return np.sqrt(1 / (2 * 10 ** (ebn0_db / 10)))


def theory_ber(ebn0_db: float) -> float:
    return 0.5 * erfc(np.sqrt(10 ** (ebn0_db / 10)))


def fig_samples(ebn0_db: float = 0.0, n: int = 40) -> None:
    """圖：送出的 ±1 與加上雜訊後收到的 r，標出判錯的點。"""
    rng = np.random.default_rng(3)
    bits = rng.integers(0, 2, n)
    s = 2 * bits - 1
    r = s + sigma_of(ebn0_db) * rng.standard_normal(n)
    err = (r > 0).astype(int) != bits
    k = np.arange(1, n + 1)

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5.6), sharex=True)
    a1.stem(k, s, linefmt="k-", markerfmt="ko", basefmt=" ")
    a1.set_ylabel("$s$")
    a1.set_ylim(-2.6, 2.6)
    a1.set_yticks([-1, 0, 1])
    a1.set_title("(a) Transmitted symbols $s \\in \\{-1, +1\\}$")

    a2.axhline(0, color="k", lw=1.5, ls="--", label="Threshold $r = 0$")
    a2.plot(k[~err], r[~err], "o", color="k", mfc="white", ms=7, label="Correct")
    a2.plot(k[err], r[err], "X", color="k", ms=10, label="Error")
    a2.set_ylabel("$r$")
    a2.set_xlabel("Sample index")
    a2.set_ylim(-2.6, 3.8)
    a2.set_yticks([-2, -1, 0, 1, 2])
    a2.set_title(f"(b) Received $r = s + n$ ($E_b/N_0$ = {ebn0_db:g} dB)")
    a2.legend(loc="upper right", ncol=3, framealpha=1)
    for a in (a1, a2):
        a.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig_samples.png", dpi=150)
    plt.close(fig)
    print(f"[done] fig_samples.png  ({ebn0_db:g} dB, {n} 個位元中錯 {err.sum()} 個)")


def fig_pdf(ebn0_list=(0.0, 4.0, 8.0), n: int = 200_000) -> None:
    """圖：不同 Eb/N0 下 r 的直方圖與理論分布，錯誤區域塗網底。"""
    rng = np.random.default_rng(2)
    x = np.linspace(-4, 4, 801)
    fig, axes = plt.subplots(1, len(ebn0_list), figsize=(13, 4.2), sharey=True)
    for i, (ax, db) in enumerate(zip(axes, ebn0_list)):
        sg = sigma_of(db)
        bits = rng.integers(0, 2, n)
        r = (2 * bits - 1) + sg * rng.standard_normal(n)
        bins = np.linspace(-4, 4, 81)
        # 直方圖：每個 s 各畫一份，縱軸換算成機率密度，再乘 1/2（兩種位元各占一半）
        for b, shade in ((0, "0.88"), (1, "0.72")):
            h, e = np.histogram(r[bits == b], bins=bins, density=True)
            ax.stairs(0.5 * h, e, fill=True, color=shade,
                      label=f"simulated, $s={2 * b - 1:+d}$" if i == 0 else None)
        p0 = 0.5 * norm.pdf(x, -1, sg)
        p1 = 0.5 * norm.pdf(x, +1, sg)
        ax.plot(x, p0, "k-", lw=1.8, label="sent $s=-1$")
        ax.plot(x, p1, "k--", lw=1.8, label="sent $s=+1$")
        ax.fill_between(x, 0, p0, where=x >= 0, facecolor="0.15", lw=0,
                        label="error region")
        ax.fill_between(x, 0, p1, where=x <= 0, facecolor="0.15", lw=0)
        if theory_ber(db) < 1e-3:
            ax.annotate("error area\ntoo small to see", xy=(0, 0.005), xytext=(1.55, 0.45),
                        fontsize=12, ha="left",
                        arrowprops=dict(arrowstyle="->", color="k", lw=1))
        ax.axvline(0, color="k", lw=1.2, ls=":")
        ax.set_xlim(-3.5, 3.5)
        ax.set_xticks([-3, -2, -1, 0, 1, 2, 3])
        ax.set_xlabel("Received value $r$")
        ax.set_title(f"$E_b/N_0$ = {db:g} dB,  $\\sigma$ = {sg:.2f}")
        ax.text(0.03, 0.95, f"BER = {theory_ber(db):.1e}", transform=ax.transAxes,
                va="top", fontsize=13, bbox=dict(fc="white", ec="0.5"))
        if i == 0:
            ax.set_ylabel("Probability density")
            ax.legend(loc="upper right", framealpha=1, fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig_pdf.png", dpi=150)
    plt.close(fig)
    print("[done] fig_pdf.png")
    for db in ebn0_list:
        print(f"       {db:g} dB: sigma = {sigma_of(db):.2f}, 理論 BER = {theory_ber(db):.1e}")


def fig_db() -> None:
    """圖：dB 與線性比值的對照，標出常用的整數點。"""
    d = np.linspace(0, 10, 201)
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    ax.plot(d, 10 ** (d / 10), "k-", lw=1.8)
    marks = [0, 3, 6, 10]
    for m in marks:
        v = 10 ** (m / 10)
        ax.plot(m, v, "o", color="k", mfc="white", ms=8)
        ax.annotate(f"{m} dB = {v:.2f}", (m, v), textcoords="offset points",
                    xytext=(-95, -4) if m == 10 else (10, -16), fontsize=12)
    ax.set_xlabel("$E_b/N_0$ (dB)")
    ax.set_ylabel("$E_b/N_0$ (linear ratio)")
    ax.set_xlim(-0.3, 10.5)
    ax.set_ylim(0, 11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig_db.png", dpi=150)
    plt.close(fig)
    print("[done] fig_db.png")
    print("       dB   線性比值   sigma")
    for m in range(0, 11):
        print(f"       {m:2d}   {10 ** (m / 10):7.2f}   {sigma_of(m):.3f}")


if __name__ == "__main__":
    fig_samples()
    fig_pdf()
    fig_db()
