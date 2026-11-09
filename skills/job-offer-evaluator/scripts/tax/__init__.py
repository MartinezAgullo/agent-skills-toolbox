"""Country tax modules. Each module exposes the same interface (see tax/base.py).

Register a new country by adding tax/<cc>.py with a `Module` class and a data/tax_<cc>.json file.
"""
import importlib

def load(country: str, regional_shift: float = 0.0):
    try:
        mod = importlib.import_module(f"tax.{country.lower()}")
    except ModuleNotFoundError:
        raise SystemExit(f"No tax module for '{country}'. Estimate manually and consider adding tax/{country.lower()}.py (see references/adding-a-country.md).")
    return mod.Module(regional_shift)
