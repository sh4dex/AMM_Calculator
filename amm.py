
def get_amount_out(amount_in, reserve_in, reserve_out):
    '''get values as float'''
    if amount_in <= 0:
        raise ValueError("amount_in should be greater than zero")
    if reserve_in <= 0:
        raise ValueError("reserve_in should be greater than zero")
    if reserve_out <= 0:
        raise ValueError("reserve_out should be greater than zero")
    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in * 1000 + amount_in_with_fee
    amount_out = numerator / denominator

    return amount_out

def get_price_impact(amount_in, reserve_in, reserve_out):
    '''get the price impact'''
    market_price = reserve_out / reserve_in
    effective_price = get_amount_out(amount_in, reserve_in, reserve_out) / amount_in
    return (market_price - effective_price) / market_price * 100

def get_swap_details(amount_in, reserve_in, reserve_out):
    '''get swap details
    It should print:
    - Market price before the swap
    - Amount out you receive
    - Effective price you paid
    - Price impact %
    - New reserves after the swap
    - New value of k (observe it grows slightly — that's LP fees accumulating)'''
    amount_out      = get_amount_out(amount_in, reserve_in, reserve_out)
    price_impact    = get_price_impact(amount_in, reserve_in, reserve_out)
    market_price    = reserve_out / reserve_in
    effective_price = amount_out / amount_in
    new_reserve_in  = reserve_in + amount_in
    new_reserve_out = reserve_out - amount_out
    new_k           = new_reserve_in * new_reserve_out
    return market_price, amount_out, effective_price, price_impact, new_reserve_in, new_reserve_out, new_k

def get_swap_formated(amount_in,reserve_in,reserve_out, token_in, token_out):
    '''swap details formattted'''
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

#print(get_amount_out(1,1000,2000000))
print(get_price_impact(1,1000,2000000))
token_in = "ETH"
token_out = "USDC"
reserve_in = 1000
reserve_out = 2000000
amount_in = 1
print(get_swap_formated(amount_in,reserve_in,reserve_out, token_in, token_out))