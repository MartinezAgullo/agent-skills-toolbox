"""Interface every country module implements (kept tiny on purpose)."""
from typing import Protocol, Tuple


class TaxModule(Protocol):
    params: dict

    def employee_net(self, gross: float) -> Tuple[float, float, float]:
        """Return (net, social_security, income_tax) for an annual gross salary."""

    def self_employed_net(self, revenue: float, expenses: float) -> Tuple[float, float, float]:
        """Return (net, social_security_or_cuota, income_tax) for annual freelance revenue."""

    def staleness(self, today) -> str | None:
        """Return a warning string if the data is out of date, else None."""
