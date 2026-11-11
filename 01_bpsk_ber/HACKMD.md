# 實作筆記 01｜BPSK 在 AWGN 通道下的位元錯誤率模擬

:::info
- 目標：以 Python 模擬 BPSK 在 AWGN 通道下的位元錯誤率，並與理論值比對（圖 1）。
- 先備知識：能在終端機執行指令。
- 程式：`~/study/handson/01_bpsk_ber/`
:::

---

## 1. 前言

無線訊號在傳輸過程中會受到雜訊 (noise) 干擾，使接收端將部分位元判錯。位元錯誤率 (Bit Error Rate, BER) 定義為判錯的位元數占傳送位元總數的比例：

$$
\text{BER} = \frac{N_{\text{error}}}{N_{\text{total}}} \tag{1}
$$

BER 對訊雜比的曲線是比較調變與編碼方式時最常用的效能指標。本篇以二進位相移鍵控 (Binary Phase Shift Keying, BPSK) 為例，建立模擬流程並與理論公式比對。

---

## 2. 系統模型

### 2.1 BPSK 調變

BPSK 將位元 $b \in \{0, 1\}$ 對應為符號 (symbol) $s \in \{-1, +1\}$：

$$
s = 2b - 1 \tag{2}
$$

### 2.2 AWGN 通道

加成性白高斯雜訊 (Additive White Gaussian Noise, AWGN) 通道的接收訊號為：

$$
r = s + n,\quad n \sim \mathcal{N}(0, \sigma^2) \tag{3}
$$

雜訊 $n$ 為平均 0、變異數 $\sigma^2$ 的高斯隨機變數，且各符號的雜訊彼此獨立。

### 2.3 判決

接收端以 0 為門檻判決：$r > 0$ 判為位元 1，$r \le 0$ 判為位元 0。當雜訊使 $r$ 越過門檻時，即產生位元錯誤。

### 2.4 Eb/N0 與雜訊變異數

$E_b/N_0$ 為每位元能量 $E_b$ 與雜訊功率頻譜密度 (noise power spectral density) $N_0$ 的比值，通常以分貝 (dB) 表示：

$$
\frac{E_b}{N_0} = 10^{(E_b/N_0)_{\text{dB}}/10} \tag{4}
$$

BPSK 為一維訊號，雜訊每維的變異數為 $N_0/2$ [1]。取 $E_b = 1$，得：

$$
\sigma^2 = \frac{N_0}{2} = \frac{1}{2\,(E_b/N_0)} \tag{5}
$$

### 2.5 理論 BER

BPSK 在 AWGN 通道下的位元錯誤率為 [1]：

$$
P_b = Q\!\left(\sqrt{\frac{2E_b}{N_0}}\right) = \frac{1}{2}\,\mathrm{erfc}\!\left(\sqrt{\frac{E_b}{N_0}}\right) \tag{6}
$$

其中 $Q(\cdot)$ 為標準常態分布的右尾機率，$\mathrm{erfc}(\cdot)$ 為互補誤差函數 (complementary error function)。

**表 1　符號定義**

| 符號 | 定義 | 本篇設定 |
|---|---|---|
| $b$ | 傳送位元 | 0 或 1 |
| $s$ | BPSK 符號 | $\pm 1$ |
| $n$ | 高斯雜訊 | $\mathcal{N}(0, \sigma^2)$ |
| $r$ | 接收訊號 | $s + n$ |
| $E_b$ | 每位元能量 | 1 |
| $E_b/N_0$ | 每位元訊雜比 | 0–9 dB |

---

## 3. 模擬流程

```mermaid
flowchart LR
    A["產生位元 b"] --> B["BPSK 調變<br/>s = 2b − 1"]
    B --> C["AWGN 通道<br/>r = s + n"]
    C --> D["判決<br/>r > 0 → 1"]
    D --> E["計算 BER"]
```

**圖 2**　模擬流程。每個 $E_b/N_0$ 執行一次，得到一個 BER 值。

---

## 4. 環境

套件由 uv 依 `check.py` 開頭的宣告自動安裝。

| 檔案 | 用途 |
|---|---|
| `ber.py` | 模擬程式 |
| `check.py` | 執行模擬、比對理論值、繪製圖 1 |
| `exercise/ber_todo.py` | 練習版，關鍵程式碼留空 |

---

## 5. 程式碼

```python=
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
```

| 行 | 說明 |
|---|---|
| 6 | 產生 `n_bits` 個均勻分布的 0/1 位元。 |
| 7 | 以向量運算一次完成所有位元的 BPSK 對應。 |
| 8 | dB 換算為線性比值。 |
| 9 | 由 $E_b/N_0$ 計算雜訊標準差。 |
| 10 | `standard_normal` 產生 $\mathcal{N}(0,1)$ 亂數，乘上 $\sigma$ 後加到符號上。 |
| 11 | 門檻判決，布林陣列轉為 0/1。 |
| 12 | 判決結果與原始位元逐一比對，錯誤比例即為 BER。 |

---

## 6. 結果

```bash
cd ~/study/handson/01_bpsk_ber
uv run check.py
```

![](ber_expected.png)

**圖 1**　BPSK 在 AWGN 通道下的 BER。實線為式 (6)，圓點為模擬值，每點傳送 $10^6$ 個位元。

模擬值在 0–9 dB 範圍內與理論值一致。$E_b/N_0 = 0$ dB 時 BER 為 $7.9 \times 10^{-2}$，9 dB 時降至 $3.4 \times 10^{-5}$。

10 dB 的理論 BER 為 $3.9 \times 10^{-6}$，以 $10^6$ 個位元模擬時預期錯誤數僅約 4 個，估計值的變異過大，故未列入。模擬 BER 的可信度取決於錯誤數，一般需累積約 100 個錯誤，所需位元數約為 $100 / P_b$。

---

## 7. 常見錯誤

| 現象 | 原因 |
|---|---|
| 曲線整體水平偏移 | 未將 dB 換算為線性值（式 (4)） |
| 模擬 BER 高於理論值 | 雜訊變異數誤用 $N_0$，應為 $N_0/2$（式 (5)） |
| BER 接近 1 | 判決方向與式 (2) 的對應相反 |
| BER 固定在 0.5 附近 | 判決結果與非同一批位元比對 |

---

## 8. 練習

1. 完成 `exercise/ber_todo.py` 的三處空白，以 `uv run check.py --todo` 驗證。
2. 將調變改為 QPSK，比較相同 $E_b/N_0$ 下的 BER。
3. 在式 (3) 中加入瑞利衰落 (Rayleigh fading) 係數，觀察 BER 曲線斜率的變化。

---

## 參考資料

[1] J. G. Proakis and M. Salehi, *Digital Communications*, 5th ed. New York, NY, USA: McGraw-Hill, 2008.
