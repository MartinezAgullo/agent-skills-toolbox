"""Spain: net pay for an employee (IRPF + Seguridad Social) and for an autonomo (RETA cuota + IRPF).

Approximate, annual basis. All numbers live in data/tax_es.json (state side) and
data/tax_es_regions.json (one record per autonomous community); this file only holds the rules.
Amounts are in EUR.

Terms used below:
  IRPF       Spanish personal income tax, a progressive scale applied to taxable income. It has TWO
             parts that are added: the STATE scale (art. 63 Ley 35/2006, the same everywhere) and the
             AUTONOMIC scale, which each autonomous community regulates for itself.
  region     the community of FISCAL RESIDENCE (where the taxpayer lives on 31 December), not the place
             of work nor the employer's seat. It selects the autonomic scale and the autonomic
             personal minimum. See es_regions.py.
  fallback   for a community without data (any other community, a foral regime, Ceuta/Melilla, or no
             region given) the autonomic scale is taken equal to the state scale, i.e. the combined
             IRPF scale is twice the state one, and approximation_warnings() says so.
  SS         employee social security contributions, a flat share of gross salary up to a cap.
  RETA/cuota monthly social security fee paid by autonomos (self-employed). Its size depends on the
             monthly net yield, in tramos (brackets).
  regional_shift  OPTIONAL manual adjustment, a percentage-point shift added to every rate of the
             AUTONOMIC scale (e.g. -0.01 lowers every autonomic rate by 1 point). It is applied on top
             of whatever autonomic scale is in use; it is not needed when the region has real data.
"""
import json
from datetime import date
from pathlib import Path

from . import es_regions
from .scale import tax_net_of_minimum

DATA = Path(__file__).resolve().parents[2] / "data" / "tax_es.json"


class Module:
    currency = "EUR"
    self_employed_label = "autónomo (RETA)"   # what this country calls the `self_employed` status

    supports_region = True    # `region` selects an autonomous community (see es_regions.py)

    def __init__(self, regional_shift: float = 0.0, region: str | None = None):
        """Load the Spanish tax data and pick the autonomic scale for `region` (fiscal residence).

        `region` is free text ("Madrid", "Cataluña", "Valencia"...). Without data for it the autonomic
        scale falls back to the state scale (see module docstring). `regional_shift` is the optional
        manual adjustment described in the module docstring.
        """
        self.params = json.loads(DATA.read_text(encoding="utf-8"))
        self.shift = regional_shift
        self.choice = es_regions.resolve(region, es_regions.load_regions(), self.params["regions_not_modelled"])
        self.state_scale = self.params["irpf_state_scale"]
        self.state_minimum = self.params["personal_minimum"]
        record = self.choice.data
        self.regional_scale = record["scale"] if record else self.state_scale
        self.regional_minimum = record.get("personal_minimum", self.state_minimum) if record else self.state_minimum

    def irpf_breakdown(self, base: float) -> tuple[float, float]:
        """IRPF on `base` split as (state part, autonomic part), each net of its own personal minimum.

        The state part always uses the state scale and minimum (5,550). The autonomic part uses the
        community's scale and, where the community sets one, its own personal minimum; the optional
        regional shift only touches this autonomic part.
        """
        state = tax_net_of_minimum(self.state_scale, base, self.state_minimum)
        regional = tax_net_of_minimum(self.regional_scale, base, self.regional_minimum, self.shift)
        return state, regional

    def _irpf_net_of_minimum(self, base: float) -> float:
        """Total IRPF on `base`: state part plus autonomic part (see `irpf_breakdown`)."""
        return sum(self.irpf_breakdown(base))

    def employee_net(self, gross):
        """Net pay of an employee. Returns (net, social_security, irpf).

        Steps: employee SS = rate * gross (capped at the maximum contribution base); taxable base =
        gross - SS - standard work expenses (2,000 EUR); IRPF on that base. Employer-side SS is not
        counted because it is paid by the company on top of the gross.
        """
        p = self.params
        ss = min(gross, p["ss_base_cap_annual"]) * p["ss_employee_rate"]
        tax = self._irpf_net_of_minimum(gross - ss - p["employee_other_expenses"])
        return gross - ss - tax, ss, tax

    def self_employed_net(self, revenue, expenses):
        """Net income of an autonomo. Returns (net, cuota_for_the_year, irpf).

        Steps: monthly net yield = (revenue - expenses) / 12; look up the monthly cuota in the tramo
        table (this assumes the MINIMUM base of the tramo; choosing a higher base costs more); the cuota
        is itself deductible; a further 5% (max 2,000 EUR) is deducted for hard-to-justify expenses;
        IRPF on the result. Quarterly VAT is ignored: it is collected and handed over, not income.
        """
        p = self.params
        monthly = (revenue - expenses) / 12
        cuota = next(c for top, c in p["autonomo_tramos_monthly_net_yield_to_cuota"]
                     if top is None or monthly <= top) * 12   # None = open-ended top tramo
        base = revenue - expenses - cuota
        base -= min(base * p["autonomo_hard_to_justify_rate"], p["autonomo_hard_to_justify_cap"])
        tax = self._irpf_net_of_minimum(base)
        return revenue - expenses - cuota - tax, cuota, tax

    def staleness_items(self, today=None) -> list[str]:
        """Separate staleness notes: first Spain's general data, then the chosen community's (so callers can de-duplicate)."""
        today = today or date.today()
        items = []
        if today.year > self.params["tax_year"]:
            items.append(f"Spanish tax data is for {self.params['tax_year']}; refresh it for {today.year}.")
        elif self.params.get("unverified"):
            items.append("Spanish tax data refreshed " + self.params["verified_on"]
                         + "; still unverified: " + "; ".join(self.params["unverified"]) + ".")
        items.extend(self._region_staleness(today))
        return items

    def staleness(self, today=None):
        """Warn when data is behind the calendar or partly unverified, for Spain and for the chosen community."""
        return " ".join(self.staleness_items(today)) or None

    def _region_staleness(self, today) -> list[str]:
        """Staleness notes for the selected community only (nothing when it has no data: see approximation_warnings)."""
        record = self.choice.data
        if not record:
            return []
        if today.year > record["tax_year"]:
            return [f"The {record['name']} IRPF scale is for {record['tax_year']}; refresh data/tax_es_regions.json for {today.year}."]
        if record["unverified"]:
            return [f"{record['name']} IRPF data (verified {record['verified_on']}) still unverified: "
                    + "; ".join(record["unverified"]) + "."]
        return []

    def approximation_warnings(self) -> list[str]:
        """Notices about approximations in use: today, the state-scale fallback when the community has no data."""
        warning = es_regions.fallback_warning(self.choice)
        return [warning] if warning else []
