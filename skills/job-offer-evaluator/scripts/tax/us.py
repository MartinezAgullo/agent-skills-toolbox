"""United States: net pay for a W-2 employee and for a 1099 (self-employed) worker.

Federal tax computed from data/tax_us.json, plus a state tax that the user supplies as one rate.
Amounts are in USD.

Assumptions (all approximate): single filer, standard deduction, no pre-tax 401(k)/HSA, no itemising,
no QBI (20% pass-through) deduction (conservative for 1099), employer-side payroll taxes ignored.

Terms used below:
  FICA        payroll taxes withheld from an employee: Social Security (6.2%, up to a yearly wage
              base) + Medicare (1.45%, no cap) + an extra 0.9% Medicare above 200k.
  SE tax      "self-employment tax": what a 1099 worker pays for both the employee and the employer
              half (12.4% + 2.9%), computed on 92.35% of profit. Half of it is deductible from income.
  AGI         adjusted gross income: income after above-the-line deductions, before the standard one.
  regional_shift  here it is the average STATE income tax rate (about 0 for TX/FL/WA, roughly
              0.04-0.06 elsewhere), applied to federal taxable income. States are not modelled one by one.
"""
import json
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "tax_us.json"


class Module:
    currency = "USD"
    self_employed_label = "1099 / sole proprietor"   # what this country calls the `self_employed` status

    def __init__(self, regional_shift: float = 0.0):
        """Load the US tax data; `regional_shift` is the state income tax rate (see module docstring)."""
        self.params = json.loads(DATA.read_text())
        self.state_rate = regional_shift

    def _federal(self, taxable: float) -> float:
        """Federal income tax: progressive brackets, each slice taxed at its own rate (single filer)."""
        tax, prev = 0.0, 0.0
        for top, rate in self.params["federal_scale_single"]:
            top = float("inf") if top is None else top   # last bracket has no upper limit
            if taxable > prev:
                tax += (min(taxable, top) - prev) * rate
            prev = top
        return tax

    def _income_tax(self, agi: float) -> float:
        """Federal + state income tax for a given AGI: subtract the standard deduction, then tax what is left."""
        taxable = max(agi - self.params["standard_deduction"], 0)
        return self._federal(taxable) + taxable * self.state_rate

    def employee_net(self, gross):
        """Net pay of a W-2 employee. Returns (net, fica, federal_plus_state_income_tax).

        FICA = Social Security (capped at the wage base) + Medicare + the extra 0.9% Medicare above the
        threshold. Income tax is computed on the full gross (no 401(k) or other pre-tax deductions).
        The employer's half of FICA is paid by the company and is not part of the gross.
        """
        p = self.params
        fica = (min(gross, p["ss_wage_base"]) * p["ss_rate_employee"]
                + gross * p["medicare_rate_employee"]
                + max(gross - p["additional_medicare_threshold_single"], 0) * p["additional_medicare_rate"])
        tax = self._income_tax(gross)
        return gross - fica - tax, fica, tax

    def self_employed_net(self, revenue, expenses):
        """Net income of a 1099 worker. Returns (net, se_tax, federal_plus_state_income_tax).

        `expenses` must include costs the worker pays alone, notably health insurance, which an employer
        would normally cover. SE tax applies to 92.35% of profit: 12.4% Social Security up to the wage
        base, 2.9% Medicare without cap, plus the extra 0.9% above the threshold. Half of SE tax lowers
        taxable income; income tax is then computed on the rest.
        """
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
        """Warn when the data year is behind the calendar; otherwise None."""
        today = today or date.today()
        if today.year > self.params["tax_year"]:
            return f"US tax data is for {self.params['tax_year']}; refresh it for {today.year}."
        return None
