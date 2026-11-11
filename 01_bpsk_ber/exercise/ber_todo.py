"""BPSK 在 AWGN 通道下的位元錯誤率 (Bit Error Rate, BER) 模擬。

把三個 TODO 填完，然後在上一層目錄執行 `uv run check.py --todo`。
"""
import numpy as np
from scipy.special import erfc


def simulate_ber(ebn0_db: float, n_bits: int, rng: np.random.Generator) -> float:
    bits = rng.integers(0, 2, n_bits)

    # TODO 1：把位元對應成 BPSK 符號：0 -> -1，1 -> +1
    symbols = None

    # TODO 2：依 Eb/N0（dB）算出雜訊標準差 sigma，加上高斯雜訊
    #   提示：符號能量 Eb = 1；雜訊每一維的變異數是 N0/2
    ebn0 = 10 ** (ebn0_db / 10)
    sigma = None
    received = None

    # TODO 3：判決（大於 0 判成 1），算出錯誤比例
    decided = None
    return None


def theory_ber(ebn0_db):
    """理論值 Pb = Q(sqrt(2 Eb/N0)) = 0.5 * erfc(sqrt(Eb/N0))。"""
    return 0.5 * erfc(np.sqrt(10 ** (np.asarray(ebn0_db) / 10)))
