"""Spain: employee (IRPF + SS) and autonomo (RETA cuota + IRPF). Approximate, annual basis."""
import json
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "tax_es.json"


class Module:
    def __init__(self, regional_shift: float = 0.0):
        self.params = json.loads(DATA.read_text())
        self.shift = regional_shift

    def _irpf(self, base: float) -> float:
        tax, prev = 0.0, 0.0
        for top, rate in self.params["irpf_scale"]:
            top = float("inf") if top is None else top
            if base > prev:
                tax += (min(base, top) - prev) * max(rate + self.shift, 0)
            prev = top
        return tax

    def _irpf_net_of_minimum(self, base: float) -> float:
        return max(self._irpf(base) - self._irpf(self.params["personal_minimum"]), 0)

    def employee_net(self, gross):
        p = self.params
        ss = min(gross, p["ss_base_cap_annual"]) * p["ss_employee_rate"]
        tax = self._irpf_net_of_minimum(gross - ss - p["employee_other_expenses"])
        return gross - ss - tax, ss, tax

    def self_employed_net(self, revenue, expenses):
        p = self.params
        monthly = (revenue - expenses) / 12
        cuota = next(c for top, c in p["autonomo_tramos_monthly_net_yield_to_cuota"]
                     if top is None or monthly <= top) * 12
        base = revenue - expenses - cuota
        base -= min(base * p["autonomo_hard_to_justify_rate"], p["autonomo_hard_to_justify_cap"])
        tax = self._irpf_net_of_minimum(base)
        return revenue - expenses - cuota - tax, cuota, tax

    def staleness(self, today=None):
        today = today or date.today()
        if today.year > self.params["tax_year"] + 1 or "NOT checked" in self.params["verified_by"] or "NOT" in self.params["verified_by"]:
            return (f"Tax data is for {self.params['tax_year']} and was not verified against official sources "
                    f"(last touched {self.params['verified_on']}). Run the refresh procedure before trusting the numbers.")
        if today.year > self.params["tax_year"]:
            return f"Tax data is for {self.params['tax_year']}; a new year is available. Refresh it."
        return None
