"""Interface every country tax module implements."""
from typing import Protocol, Tuple


class TaxModule(Protocol):
    """What `net_compare.py` expects from a country module (see `tax/__init__.py:load`).

    Both calculation methods return a 3-tuple `(net, social, income_tax)` in the module's own
    currency, for ONE full year. `net` is what ends up in the person's pocket.
    """

    params: dict      # the country's numbers, loaded from data/tax_<cc>.json
    currency: str     # ISO code of the amounts this module works in, e.g. "EUR", "USD"
    self_employed_label: str  # local name of the self_employed status, e.g. "autónomo (RETA)", "1099 / sole proprietor"
    supports_region: bool     # optional: True if the constructor accepts a named `region` (Spain: autonomous community)

    def employee_net(self, gross: float) -> Tuple[float, float, float]:
        """Return (net, social_security, income_tax) for an annual gross salary."""

    def self_employed_net(self, revenue: float, expenses: float) -> Tuple[float, float, float]:
        """Return (net, social_security_or_cuota, income_tax) for annual self-employed revenue (autónomo, 1099, "freelance"...).

        `expenses` are business costs deducted before tax (gestor, insurance, tools...).
        """

    def staleness(self, today) -> str | None:
        """Return a warning string if the data is out of date or partly unverified, else None."""

    def approximation_warnings(self) -> list[str]:
        """Optional. Notices about approximations in use (e.g. Spain: no data for the community, state-scale fallback)."""

    def staleness_items(self, today=None) -> list[str]:
        """Optional. The same notes as `staleness`, as a list so callers can drop repeats across two modules."""
