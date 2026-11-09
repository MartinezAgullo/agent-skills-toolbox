"""Spain: net pay for an employee (IRPF + Seguridad Social) and for an autonomo (RETA cuota + IRPF).

Approximate, annual basis. All numbers live in data/tax_es.json; this file only holds the rules.
Amounts are in EUR.

Terms used below:
  IRPF       Spanish personal income tax, a progressive scale applied to taxable income.
  SS         employee social security contributions, a flat share of gross salary up to a cap.
  RETA/cuota monthly social security fee paid by autonomos (self-employed). Its size depends on the
             monthly net yield, in tramos (brackets).
  regional_shift  IRPF has a state part and a regional part, and each autonomous community sets its own
             regional scale. The data file holds ONE combined scale, so the region is approximated by a
             percentage-point shift applied to every bracket (e.g. -0.01 lowers every rate by 1 point).
"""
import json
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "tax_es.json"


class Module:
    currency = "EUR"
    self_employed_label = "autónomo (RETA)"   # what this country calls the `self_employed` status

    def __init__(self, regional_shift: float = 0.0):
        """Load the Spanish tax data; `regional_shift` adjusts every IRPF rate (see module docstring)."""
        self.params = json.loads(DATA.read_text())
        self.shift = regional_shift

    def _irpf(self, base: float) -> float:
        """Apply the progressive IRPF scale to `base`: each slice of income is taxed at its own rate.

        Example: with brackets 19% up to 12,450 and 24% up to 20,200, a base of 15,000 pays
        12,450 * 19% + 2,550 * 24%. The regional shift is added to every rate (never below 0).
        """
        tax, prev = 0.0, 0.0
        for top, rate in self.params["irpf_scale"]:
            top = float("inf") if top is None else top   # last bracket has no upper limit
            if base > prev:
                tax += (min(base, top) - prev) * max(rate + self.shift, 0)
            prev = top
        return tax

    def _irpf_net_of_minimum(self, base: float) -> float:
        """IRPF on `base` after the personal minimum (5,550 EUR).

        The minimum is not subtracted from income: Spain computes the tax on the whole base, then
        subtracts the tax that the minimum itself would generate. That is what this does.
        """
        return max(self._irpf(base) - self._irpf(self.params["personal_minimum"]), 0)

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

    def staleness(self, today=None):
        """Warn when the data year is behind the calendar, or list what is still unverified."""
        today = today or date.today()
        if today.year > self.params["tax_year"]:
            return f"Spanish tax data is for {self.params['tax_year']}; refresh it for {today.year}."
        items = self.params.get("unverified")
        if items:
            return "Spanish tax data refreshed " + self.params["verified_on"] + "; still unverified: " + "; ".join(items) + "."
        return None
