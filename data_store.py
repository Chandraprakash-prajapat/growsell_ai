"""Holds the seller's uploaded Meesho payment data in memory (never written to disk).

One seller uses the tool at a time, so one shared store is enough. The data is lost when
the server restarts, and "Clear my data" removes it at any time.
"""

DEFAULT_COST = 95.0

_STATE = {"rows": None, "ads_cost": 0.0, "file_name": "", "default_cost": DEFAULT_COST, "costs": {}}


def has_real():
    """True when the seller has uploaded a payment file."""
    return bool(_STATE["rows"])


def set_real(rows, ads_cost, file_name):
    """Save the parsed payment rows and the ads cost."""
    _STATE.update(rows=rows, ads_cost=ads_cost, file_name=file_name)


def clear():
    """Forget the uploaded data (the tool falls back to the demo data)."""
    _STATE.update(rows=None, ads_cost=0.0, file_name="", default_cost=DEFAULT_COST, costs={})


def get_state():
    """Return the stored data."""
    return _STATE


def set_costs(default_cost, costs):
    """Set the product cost per piece: one default plus optional per-SKU costs."""
    _STATE["default_cost"] = float(default_cost)
    _STATE["costs"] = {k: float(v) for k, v in costs.items()}
