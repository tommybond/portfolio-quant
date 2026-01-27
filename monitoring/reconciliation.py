
from monitoring.audit import log_event

def reconcile(strategy, broker):
    mismatches = []
    for t in strategy:
        if t not in broker:
            mismatches.append(t)
    if mismatches:
        log_event("RECON_FAIL", mismatches)
    else:
        log_event("RECON_OK", "All matched")
    return mismatches
