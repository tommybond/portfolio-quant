
def execution_price(price, qty, adv, spread, impact_factor=0.1):
    impact = impact_factor * (qty / adv)
    return price * (1 + spread + impact)
