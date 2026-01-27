
def correlation_adjusted_size(base_size, asset_corr, threshold=0.6):
    if asset_corr > threshold:
        return base_size * 0.5
    elif asset_corr < 0.3:
        return base_size * 1.2
    return base_size
