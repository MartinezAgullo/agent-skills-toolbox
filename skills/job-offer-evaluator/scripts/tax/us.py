"""United States: W-2 employee and 1099/self-employed, federal only plus a user-supplied state rate.

Assumptions (all approximate): single filer, standard deduction, no pre-tax 401(k)/HSA, no itemising,
no QBI (20% pass-through) deduction (conservative for 1099), employer-side payroll taxes ignored.
`regional_shift` is the average state income tax rate applied to federal taxable income
(about 0 for TX/FL/WA, roughly 0.04-0.06 for many states). Amounts are in USD.
"""
import json
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "tax_us.json"


class Module:
    currency = "USD"

    def __init__(self, regional_shift: float = 0.0):
        self.params = json.loads(DATA.read_text())
        self.state_rate = regional_shift

    def _federal(self, taxable: float) -> float:
        tax, prev = 0.0, 0.0
        for top, rate in self.params["federal_scale_single"]:
            top = float("inf") if top is None else top
            if taxable > prev:
                tax += (min(taxable, top) - prev) * rate
            prev = top
        return tax

    def _income_tax(self, agi: float) -> float:
        taxable = max(agi - self.params["standard_deduction"], 0)
        return self._federal(taxable) + taxable * self.state_rate

    def employee_net(self, gross):
        p = self.params
        fica = (min(gross, p["ss_wage_base"]) * p["ss_rate_employee"]
                + gross * p["medicare_rate_employee"]
                + max(gross - p["additional_medicare_threshold_single"], 0) * p["additional_medicare_rate"])
        tax = self._income_tax(gross)
        return gross - fica - tax, fica, tax

    def self_employed_net(self, revenue, expenses):
        p = self.params
        profit = max(revenue - expenses, 0)
        base = profit * p["se_net_earnings_factor"]
        se_tax = (min(base, p["ss_wage_base"]) * p["ss_rate_self_employed"]
                  + base * p["medicare_rate_self_employed"]
                  + max(base - p["additional_medicare_threshold_single"], 0) * p["additional_medicare_rate"])
        agi = profit - se_tax / 2          # half of SE tax is deductible
        tax = self._income_tax(agi)
        return profit - se_tax - tax, se_tax, tax

    def staleness(self, today=None):
        today = today or date.today()
        if today.year > self.params["tax_year"]:
            return f"US tax data is for {self.params['tax_year']}; refresh it for {today.year}."
        return None
