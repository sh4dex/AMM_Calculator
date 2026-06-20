# AMM Calculator — Uniswap V2

> Interactive calculator that simulates swaps against the Uniswap V2 WETH/USDC pool using real on-chain reserves. Built to understand how the `x * y = k` invariant works under the hood.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Dash](https://img.shields.io/badge/dash-interactive-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**🚀 Live demo:** [ammcalculator-production.up.railway.app](https://ammcalculator-production.up.railway.app)

## What it does

- 🔗 Pulls live reserves from Ethereum mainnet via RPC
- 🔄 Simulates any ETH → USDC swap with the exact Uniswap V2 formula (including the 0.3% fee)
- 📊 Shows market price, effective price, price impact, and post-swap pool state
- 📈 Plots the **effective price curve** against market price so you can see the hyperbola bend as swap size grows

## Project structure

```
src/
├── amm.py      # Pure math — Uniswap V2 formula, no blockchain dependency
├── reader.py   # Reads live reserves from Ethereum via web3.py
├── app.py      # Dash interactive UI
└── main.py     # Entry point — exposes the WSGI `server` for gunicorn
```
## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
cd src
python main.py
```

Open **http://127.0.0.1:8050** in your browser.

### Configuration

| Env var | Default | Description |
|---|---|---|
| `PORT` | `8050` | Port the app listens on. Set automatically by Railway. |
| `RPC_URL` | `https://eth.blockrazor.xyz` | Ethereum HTTP RPC endpoint used to read live reserves. Override with a dedicated provider (Alchemy, Infura, …) for reliability. |

If the RPC endpoint is unreachable at startup, the app falls back to sensible default reserves so it still boots.

## Deployment (Railway)

The repo is deploy-ready for [Railway](https://railway.app):

- **`requirements.txt`** — pinned dependencies, including `gunicorn`.
- **`Procfile` / `railway.json`** — start command served by gunicorn:
  ```
  gunicorn --chdir src main:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120
  ```
- **`.python-version`** — pins Python 3.12 for the build.

To deploy: connect the GitHub repo in Railway, then **Settings → Networking → Generate Domain** to expose the public URL. Set `RPC_URL` under **Variables** if you want a dedicated node.

## How to use

### Sliders

| Slider | What it controls |
|---|---|
| **Amount In (ETH)** | How much ETH you're swapping. Auto-scales to 80% of WETH reserve so the curve always shows its characteristic bend. |
| **Reserve WETH** | WETH held in the pool. Defaults to live on-chain value. Smaller pool = more price impact for the same swap size. |
| **Reserve USDC** | USDC held in the pool. Affects amount out and market price but not the shape of the price impact curve (`reserve_out` cancels out mathematically). |

### Metric cards

| Card | What it means |
|---|---|
| **Market Price** | Current spot price of ETH in the pool — `reserve_usdc / reserve_weth`. This is what you'd get for an infinitely small swap. |
| **Amount Out** | USDC you receive for the selected ETH amount, after the 0.3% fee. |
| **Effective Price** | Actual price paid — `amount_out / amount_in`. Always slightly worse than market price. |
| **Price Impact** | How much worse your effective price is vs market price, as a percentage. Under 1% is normal; above 5% is significant slippage. |

### The `k` bar

After every swap, `k = reserve_in * reserve_out` grows slightly. That growth is the 0.3% fee staying in the pool — it's how liquidity providers earn yield without any token minting.

### The chart

| Element | Meaning |
|---|---|
| Gray dotted line | Market price (flat, doesn't depend on swap size) |
| Red curve | Effective price you actually get at each swap size |
| Green vertical line | Your current selected amount |

The gap between the two lines is the price impact. As the curve bends toward zero, you're approaching the pool's full liquidity — in practice, no one swaps more than a few percent of the pool.

## The math

Uniswap V2 applies the fee by scaling integers instead of using decimals:

```
amount_in_with_fee = amount_in × 997
numerator          = amount_in_with_fee × reserve_out
denominator        = reserve_in × 1000 + amount_in_with_fee
amount_out         = numerator / denominator
```

This is identical to the Solidity implementation. The `× 997 / × 1000` pattern keeps the fee as integer arithmetic — no floats inside the contract.

### Why `reserve_out` doesn't affect price impact

Expanding the price impact formula:

```
price_impact = 1 - effective_price / market_price
             = 1 - (997 × reserve_in) / (reserve_in × 1000 + amount_in × 997)
```

`reserve_out` disappears. Price impact is purely a function of how large your swap is relative to `reserve_in`.

## License

MIT