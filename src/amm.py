
def get_amount_out(amount_in: float, reserve_in: float, reserve_out: float) -> float:
    """Calculate the output amount for a swap using the Uniswap V2 formula.

    Replicates the Solidity contract logic with integer-scaled fee (997/1000 = 0.3% fee):
        amountOut = (amountIn * 997 * reserveOut) / (reserveIn * 1000 + amountIn * 997)

    The *997 / *1000 pattern avoids floating-point division inside Solidity.
    In Python we keep the same integers so the result matches the on-chain value exactly.

    Args:
        amount_in: Amount of the input token to swap (human units, e.g. ETH).
        reserve_in: Current pool reserve of the input token.
        reserve_out: Current pool reserve of the output token.

    Returns:
        Amount of the output token received after the 0.3% fee.

    Raises:
        ValueError: If any argument is zero or negative.
    """
    if amount_in <= 0:
        raise ValueError("amount_in must be greater than zero")
    if reserve_in <= 0:
        raise ValueError("reserve_in must be greater than zero")
    if reserve_out <= 0:
        raise ValueError("reserve_out must be greater than zero")

    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in * 1000 + amount_in_with_fee
    return numerator / denominator


def get_price_impact(amount_in: float, reserve_in: float, reserve_out: float) -> float:
    """Calculate the price impact percentage of a swap.

    Price impact is how much worse the effective price is compared to the
    market price before the swap. Mathematically, reserve_out cancels out,
    so only the ratio of amount_in to reserve_in determines the impact.

    Args:
        amount_in: Amount of the input token to swap.
        reserve_in: Current pool reserve of the input token.
        reserve_out: Current pool reserve of the output token.

    Returns:
        Price impact as a percentage (e.g. 0.3 means 0.3%).
    """
    market_price = reserve_out / reserve_in
    effective_price = get_amount_out(amount_in, reserve_in, reserve_out) / amount_in
    return (market_price - effective_price) / market_price * 100


def get_swap_details(amount_in: float, reserve_in: float, reserve_out: float) -> tuple:
    """Compute full swap details including post-swap pool state.

    Combines get_amount_out and get_price_impact and derives the new reserve
    balances and invariant k after the swap settles.

    Args:
        amount_in: Amount of the input token to swap.
        reserve_in: Current pool reserve of the input token.
        reserve_out: Current pool reserve of the output token.

    Returns:
        Tuple of seven values:
            market_price (float):    Spot price before the swap (reserve_out / reserve_in).
            amount_out (float):      Output tokens received.
            effective_price (float): Actual price paid (amount_out / amount_in).
            price_impact (float):    Slippage as a percentage.
            new_reserve_in (float):  Pool reserve of input token after swap.
            new_reserve_out (float): Pool reserve of output token after swap.
            new_k (float):           New invariant — slightly larger than original due to fees.
    """
    amount_out      = get_amount_out(amount_in, reserve_in, reserve_out)
    price_impact    = get_price_impact(amount_in, reserve_in, reserve_out)
    market_price    = reserve_out / reserve_in
    effective_price = amount_out / amount_in
    new_reserve_in  = reserve_in + amount_in
    new_reserve_out = reserve_out - amount_out
    new_k           = new_reserve_in * new_reserve_out
    return market_price, amount_out, effective_price, price_impact, new_reserve_in, new_reserve_out, new_k


def get_swap_formated(amount_in: float, reserve_in: float, reserve_out: float,
                      token_in: str, token_out: str) -> str:
    """Format full swap details as a human-readable multi-line string.

    Intended for CLI output or the stats panel in the Dash app.
    Internally delegates all math to get_swap_details.

    Args:
        amount_in:  Amount of the input token to swap.
        reserve_in: Pool reserve of the input token.
        reserve_out: Pool reserve of the output token.
        token_in:   Symbol of the input token (e.g. "ETH").
        token_out:  Symbol of the output token (e.g. "USDC").

    Returns:
        Multi-line string with market price, amount out, effective price,
        price impact, new reserves, and new k value.
    """
    market_price, amount_out, effective_price, price_impact, new_reserve_in, new_reserve_out, new_k = \
        get_swap_details(amount_in, reserve_in, reserve_out)
    return (
        f"Market price:    {market_price:.2f} {token_out}/{token_in}\n"
        f"Amount out:      {amount_out:.2f} {token_out}\n"
        f"Effective price: {effective_price:.2f} {token_out}/{token_in}\n"
        f"Price impact:    {price_impact:.4f}%\n"
        f"New reserves:    {new_reserve_in:.2f} {token_in} / {new_reserve_out:.2f} {token_out}\n"
        f"New k:           {new_k:.2f}  (was {reserve_in * reserve_out:.2f})"
    )
