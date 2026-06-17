
from web3 import Web3

# Prefer HTTPS over WebSocket (wss://) — Web3.HTTPProvider only, no extra deps
RPC_URL = "https://eth.blockrazor.xyz"

# Uniswap V2 WETH/USDC pair on Ethereum mainnet
# token0 = USDC (0xA0b8...), token1 = WETH (0xC02a...)
# Uniswap orders tokens by address; USDC address < WETH address so USDC is token0
PAIR_ADDRESS = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"

# Minimal ABI — only the three functions we actually call.
# Using a partial ABI avoids importing the full ~200-line Pair ABI.
ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"name": "reserve0", "type": "uint112"},
        {"name": "reserve1", "type": "uint112"},
        {"name": "blockTimestampLast", "type": "uint32"}
    ], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]


def get_reserves() -> dict:
    """Fetch live reserves from the Uniswap V2 WETH/USDC pair on Ethereum mainnet.

    Connects to an Ethereum node via HTTP RPC, calls getReserves() on the pair
    contract, and converts raw uint112 values to human-readable floats:
        - USDC has 6 decimals  → divide reserve0 by 10**6
        - WETH has 18 decimals → divide reserve1 by 10**18

    Web3.to_checksum_address() is required — web3.py rejects plain lowercase addresses.

    Returns:
        dict with keys:
            usdc (float):           USDC reserve in human units.
            weth (float):           WETH reserve in human units.
            price_eth_usdc (float): Implied ETH price in USDC (usdc / weth).
            token0 (str):           Checksummed address of token0 (USDC).
            token1 (str):           Checksummed address of token1 (WETH).

    Raises:
        ConnectionError: If the RPC call fails or the node is unreachable.
    """
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(PAIR_ADDRESS),
        abi=ABI
    )
    try:
        reserves = contract.functions.getReserves().call()
        usdc = reserves[0] / 10**6
        weth = reserves[1] / 10**18
        return {
            "usdc": usdc,
            "weth": weth,
            "price_eth_usdc": usdc / weth,
            "token0": contract.functions.token0().call(),
            "token1": contract.functions.token1().call(),
        }
    except Exception as e:
        raise ConnectionError(f"Cannot connect to Ethereum node: {e}")
