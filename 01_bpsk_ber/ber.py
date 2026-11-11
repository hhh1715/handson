import numpy as np
from scipy.special import erfc


def simulate_ber(ebn0_db: float, n_bits: int, rng: np.random.Generator) -> float:
    bits = rng.integers(0, 2, n_bits)
    symbols = 2 * bits - 1                      # 式 (2)
    ebn0 = 10 ** (ebn0_db / 10)                 # 式 (4)
    sigma = np.sqrt(1 / (2 * ebn0))             # 式 (5)
    received = symbols + sigma * rng.standard_normal(n_bits)   # 式 (3)
    decided = (received > 0).astype(int)
    return np.mean(decided != bits)             # 式 (1)


def theory_ber(ebn0_db):
    return 0.5 * erfc(np.sqrt(10 ** (np.asarray(ebn0_db) / 10)))   # 式 (6)
