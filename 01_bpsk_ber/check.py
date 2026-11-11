# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy", "matplotlib"]
# ///
"""跑模擬、跟理論值比對，並畫出 BER 曲線（存成 ber.png）。

用法：uv run check.py           執行完整版 ber.py
      uv run check.py --todo    檢查你在 exercise/ber_todo.py 寫的版本
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if "--todo" in sys.argv:
    sys.path.insert(0, "exercise")
    from ber_todo import simulate_ber, theory_ber
else:
    from ber import simulate_ber, theory_ber

rng = np.random.default_rng(0)
snr = np.arange(0, 10)
sim = []
for s in snr:
    b = simulate_ber(s, 1_000_000, rng)
    if b is None:
        sys.exit("[fail] simulate_ber 回傳 None，TODO 還沒完成")
    sim.append(b)
sim = np.array(sim)
th = theory_ber(snr)

ok = True
for s, b, t in zip(snr, sim, th):
    # 誤差容許範圍隨錯誤數調整：二項分布標準差 sqrt(t/N)，取 4 倍
    good = abs(b - t) < 4 * np.sqrt(t / 1_000_000)
    ok &= good
    print(f"Eb/N0 = {s:2d} dB  模擬 {b:.2e}  理論 {t:.2e}  {'[ok]' if good else '[fail]'}")

# 實驗室圖表規範：Times New Roman（本機以字距相同的 Liberation Serif 代替）、白底、label 20 pt、legend 12 pt
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif"],
                     "mathtext.fontset": "stix", "axes.labelsize": 20, "legend.fontsize": 12,
                     "xtick.labelsize": 14, "ytick.labelsize": 14})
fig, ax = plt.subplots(figsize=(7, 5))
ax.semilogy(np.linspace(0, 10, 200), theory_ber(np.linspace(0, 10, 200)), "k-", label="Theory")
ax.semilogy(snr, np.where(sim > 0, sim, np.nan), "o", color="k", mfc="white", ms=8, label="Simulation")
ax.set_xlabel("$E_b/N_0$ (dB)")
ax.set_ylabel("BER")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig("ber.png", dpi=150)
print("\n[done] 圖存成 ber.png" if ok else "\n[fail] 有些點跟理論差太多，檢查 sigma 的算法")
