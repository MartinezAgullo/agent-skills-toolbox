#!/usr/bin/env python3
"""Net take-home comparison, current job vs offer, via country tax modules (see tax/).

Figures are APPROXIMATE. Run from anywhere: python3 scripts/net_compare.py --help
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tax as taxmods


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--country", default="ES", help="tax module to use (ES available)")
    p.add_argument("--current-gross", type=float, required=True, help="current annual gross EUR incl. variable (employee)")
    p.add_argument("--current-contract", choices=["employee", "autonomo"], default="employee")
    p.add_argument("--current-expenses", type=float, default=0, help="current autonomo yearly costs (if current-contract=autonomo)")
    p.add_argument("--current-benefits", type=float, default=0, help="yearly EUR value of current non-cash benefits (private health, meal vouchers, pension match...)")
    p.add_argument("--current-extra-costs", type=float, default=0, help="yearly out-of-pocket work costs now (commuting, equipment)")
    p.add_argument("--offer-benefits", type=float, default=0, help="yearly EUR value of offer's non-cash benefits")
    p.add_argument("--offer-extra-costs", type=float, default=0, help="yearly out-of-pocket costs in the offer (commuting, coworking, relocation)")
    p.add_argument("--irpf-shift", type=float, default=0.0, help="pp shift of IRPF rates vs average region, e.g. -0.015 Madrid, +0.01 Cataluña")
    p.add_argument("--threshold", type=float, default=None, help="minimum net uplift %% the user requires to move; verdict line is printed against it")
    p.add_argument("--offer-type", choices=["b2b", "employee"], required=True)
    p.add_argument("--offer-gross", type=float, help="employee offers: annual gross EUR")
    p.add_argument("--hourly", type=float, help="b2b: hourly rate in offer currency")
    p.add_argument("--fx", type=float, default=1.0, help="offer currency -> EUR (e.g. 0.87 for USD)")
    p.add_argument("--hours", type=float, default=1720, help="b2b billable hours/yr (unpaid vacation+holidays already removed)")
    p.add_argument("--expenses", type=float, default=1500, help="b2b yearly costs: gestor, insurance, tools")
    p.add_argument("--unpaid-gap-months", type=float, default=0, help="expected months without billing")
    a = p.parse_args()
    tm = taxmods.load(a.country, a.irpf_shift)
    warn = tm.staleness()
    if warn:
        print(f"WARNING  {warn}")
    employee_net, autonomo_net = tm.employee_net, tm.self_employed_net

    if a.current_contract == "employee":
        cur_net, ss, tax = employee_net(a.current_gross)
        print(f"CURRENT  gross {a.current_gross:,.0f} | SS {ss:,.0f} | IRPF {tax:,.0f} | NET {cur_net:,.0f} EUR/yr")
    else:
        cur_net, cuota, tax = autonomo_net(a.current_gross, a.current_expenses)
        print(f"CURRENT  revenue {a.current_gross:,.0f} | cuota {cuota:,.0f} | IRPF {tax:,.0f} | NET {cur_net:,.0f} EUR/yr")
    cur_eff = cur_net + a.current_benefits - a.current_extra_costs
    print(f"         effective (net + benefits - extra costs) {cur_eff:,.0f} EUR/yr = {cur_eff/12:,.0f}/mo")

    if a.offer_type == "b2b":
        rev = a.hourly * a.fx * a.hours * (1 - a.unpaid_gap_months / 12)
        net, cuota, tax = autonomo_net(rev, a.expenses)
        print(f"OFFER    revenue {rev:,.0f} | autonomo cuota {cuota:,.0f} | costs {a.expenses:,.0f} | IRPF {tax:,.0f} | NET {net:,.0f} EUR/yr")
    else:
        net, ss, tax = employee_net(a.offer_gross)
        print(f"OFFER    gross {a.offer_gross:,.0f} | SS {ss:,.0f} | IRPF {tax:,.0f} | NET {net:,.0f} EUR/yr")
    off_eff = net + a.offer_benefits - a.offer_extra_costs
    print(f"         effective (net + benefits - extra costs) {off_eff:,.0f} EUR/yr = {off_eff/12:,.0f}/mo")

    diff = off_eff - cur_eff
    pct = diff / cur_eff * 100
    print(f"DELTA    {diff:+,.0f} EUR/yr effective net ({pct:+.1f}%), {diff/12:+,.0f} EUR/mo")
    if a.threshold is not None:
        print(f"THRESHOLD {'MET' if pct >= a.threshold else 'NOT MET'} (required {a.threshold:+.0f}%)")
    if a.offer_type == "b2b":
        lo, hi = 0.0, 300000.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if employee_net(mid)[0] < net: lo = mid
            else: hi = mid
        print(f"EQUIV    this B2B net equals an employee gross of ~{hi:,.0f} EUR")
        print("NOTE     B2B net is BEFORE valuing lost protections (unemployment, sick pay, paid vacation, pension accrual). Cover that in the verdict.")
    print("NOTE     Spain only, approximate, annual-gross basis. 12 vs 14 payments changes cash flow, not annual net.")


if __name__ == "__main__":
    main()
