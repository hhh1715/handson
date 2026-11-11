"""BPSK 在 AWGN 通道下的位元錯誤率 (Bit Error Rate, BER) 模擬：完整版。"""
import numpy as np
from scipy.special import erfc


def simulate_ber(ebn0_db: float, n_bits: int, rng: np.random.Generator) -> float:
    bits = rng.integers(0, 2, n_bits)
    symbols = 2 * bits - 1                      # 0 -> -1, 1 -> +1
    ebn0 = 10 ** (ebn0_db / 10)
    sigma = np.sqrt(1 / (2 * ebn0))             # Eb = 1，雜訊每維變異數 N0/2
    received = symbols + sigma * rng.standard_normal(n_bits)
    decided = (received > 0).astype(int)
    return np.mean(decided != bits)


def theory_ber(ebn0_db):
    return 0.5 * erfc(np.sqrt(10 ** (np.asarray(ebn0_db) / 10)))
