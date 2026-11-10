"""Country tax modules. Each module exposes the same interface (see tax/base.py).

Register a new country by adding tax/<cc>.py with a `Module` class and a data/tax_<cc>.json file.
"""
import importlib

def load(country: str, regional_shift: float = 0.0, region: str | None = None):
    """Build the tax module for `country`.

    `regional_shift` is the country's numeric regional adjustment. `region` is a named sub-national
    region (Spain: autonomous community of fiscal residence); it is only passed to modules that
    declare `supports_region`, so callers can check that attribute to know whether it was used.
    """
    try:
        mod = importlib.import_module(f"tax.{country.lower()}")
    except ModuleNotFoundError:
        raise SystemExit(f"No tax module for '{country}'. Estimate manually and consider adding tax/{country.lower()}.py (see references/adding-a-country.md).")
    if getattr(mod.Module, "supports_region", False):
        return mod.Module(regional_shift, region=region)
    return mod.Module(regional_shift)
