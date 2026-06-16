
from web3 import Web3

RPC_URL = "https://cloudflare-eth.com"
PAIR_ADDRESS = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"name": "reserve0", "type": "uint112"},
        {"name": "reserve1", "type": "uint112"},
        {"name": "blockTimestampLast", "type": "uint32"}
    ], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

def get_reserves():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(PAIR_ADDRESS),
        abi=ABI
    )
    try:
        reserves = contract.functions.getReserves().call()
    except Exception as e:
        raise ConnectionError(f"Cannot connect to Ethereum node: {e}")

    usdc = reserves[0] / 10**6
    weth = reserves[1] / 10**18

    return {
        "usdc": usdc,
        "weth": weth,
        "price_eth_usdc": usdc / weth,
        "token0": contract.functions.token0().call(),
        "token1": contract.functions.token1().call(),
    }

if __name__ == "__main__":
    data = get_reserves()
    print(data)