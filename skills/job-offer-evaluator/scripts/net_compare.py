#!/usr/bin/env python3
"""Net take-home comparison, current job vs offer, via country tax modules (see tax/).

The current job is taxed in --country, the offer in --offer-country (default: same). Figures are
APPROXIMATE. Currency model:
  * current job amounts are in the currency of --country (EUR for ES); --current-to-eur converts if not EUR
  * offer amounts (--offer-gross, --expenses) are in the currency of --offer-country
  * --hourly is in the PAY currency; --fx converts pay currency -> offer-country currency (ES-taxed USD pay: 0.89)
  * --to-eur converts offer-country currency -> EUR (US-taxed USD pay: --fx 1 --to-eur 0.89)
  * benefits and extra costs are always in EUR
Run: python3 scripts/net_compare.py --help
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tax as taxmods


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--country", default="ES", help="tax module for the CURRENT job (ES, US)")
    p.add_argument("--offer-country", default=None, help="tax module for the OFFER (default: same as --country)")
    p.add_argument("--current-gross", type=float, required=True, help="current annual gross incl. expected variable")
    p.add_argument("--current-contract", choices=["employee", "autonomo"], default="employee")
    p.add_argument("--current-expenses", type=float, default=0, help="current self-employed yearly costs")
    p.add_argument("--current-to-eur", type=float, default=1.0, help="current country currency -> EUR")
    p.add_argument("--current-benefits", type=float, default=0, help="EUR/yr value of current non-cash benefits")
    p.add_argument("--current-extra-costs", type=float, default=0, help="EUR/yr current out-of-pocket work costs")
    p.add_argument("--offer-type", choices=["b2b", "employee"], required=True, help="b2b = freelance/1099/autonomo")
    p.add_argument("--offer-gross", type=float, help="employee offers: annual gross, offer-country currency")
    p.add_argument("--hourly", type=float, help="b2b: hourly rate in the PAY currency")
    p.add_argument("--fx", type=float, default=1.0, help="pay currency -> offer-country currency")
    p.add_argument("--to-eur", type=float, default=1.0, help="offer-country currency -> EUR")
    p.add_argument("--hours", type=float, default=1720, help="b2b billable hours/yr")
    p.add_argument("--expenses", type=float, default=1500, help="b2b yearly costs (gestor, health insurance for 1099...), offer-country currency")
    p.add_argument("--unpaid-gap-months", type=float, default=0, help="expected months without billing")
    p.add_argument("--offer-benefits", type=float, default=0, help="EUR/yr value of offer's non-cash benefits")
    p.add_argument("--offer-extra-costs", type=float, default=0, help="EUR/yr offer out-of-pocket costs")
    p.add_argument("--irpf-shift", "--region-adjust", dest="region", type=float, default=0.0,
                   help="regional adjustment for the current country (ES: IRPF pp shift e.g. -0.015 Madrid; US: avg state tax rate)")
    p.add_argument("--offer-region-adjust", type=float, default=None, help="same, for the offer country (default: --irpf-shift when same country)")
    p.add_argument("--threshold", type=float, default=None, help="minimum effective-net uplift %% required; prints MET/NOT MET")
    a = p.parse_args()

    off_cc = (a.offer_country or a.country).upper()
    off_region = a.offer_region_adjust if a.offer_region_adjust is not None else (a.region if off_cc == a.country.upper() else 0.0)
    cur = taxmods.load(a.country, a.region)
    off = taxmods.load(off_cc, off_region)
    cur_ccy, off_ccy = getattr(cur, "currency", "EUR"), getattr(off, "currency", "EUR")

    warnings = []
    for tm in (cur, off):
        w = tm.staleness()
        if w and w not in warnings:
            warnings.append(w)
    for w in warnings:
        print(f"WARNING  {w}")

    # current job
    if a.current_contract == "employee":
        net_l, soc, tax = cur.employee_net(a.current_gross)
        print(f"CURRENT [{a.country.upper()}, {cur_ccy}]  gross {a.current_gross:,.0f} | social/payroll {soc:,.0f} | income tax {tax:,.0f} | NET {net_l:,.0f}")
    else:
        net_l, soc, tax = cur.self_employed_net(a.current_gross, a.current_expenses)
        print(f"CURRENT [{a.country.upper()}, {cur_ccy}]  revenue {a.current_gross:,.0f} | social {soc:,.0f} | income tax {tax:,.0f} | NET {net_l:,.0f}")
    cur_eff = net_l * a.current_to_eur + a.current_benefits - a.current_extra_costs
    print(f"         effective EUR (net + benefits - extra costs): {cur_eff:,.0f}/yr = {cur_eff/12:,.0f}/mo")

    # offer
    if a.offer_type == "b2b":
        rev = a.hourly * a.fx * a.hours * (1 - a.unpaid_gap_months / 12)
        o_net, o_soc, o_tax = off.self_employed_net(rev, a.expenses)
        print(f"OFFER   [{off_cc}, {off_ccy}]  revenue {rev:,.0f} | costs {a.expenses:,.0f} | social/SE tax {o_soc:,.0f} | income tax {o_tax:,.0f} | NET {o_net:,.0f}")
    else:
        o_net, o_soc, o_tax = off.employee_net(a.offer_gross)
        print(f"OFFER   [{off_cc}, {off_ccy}]  gross {a.offer_gross:,.0f} | social/payroll {o_soc:,.0f} | income tax {o_tax:,.0f} | NET {o_net:,.0f}")
    o_net_eur = o_net * a.to_eur
    off_eff = o_net_eur + a.offer_benefits - a.offer_extra_costs
    print(f"         effective EUR (net + benefits - extra costs): {off_eff:,.0f}/yr = {off_eff/12:,.0f}/mo")

    diff = off_eff - cur_eff
    pct = diff / cur_eff * 100
    print(f"DELTA    {diff:+,.0f} EUR/yr effective net ({pct:+.1f}%), {diff/12:+,.0f} EUR/mo")
    if a.threshold is not None:
        print(f"THRESHOLD {'MET' if pct >= a.threshold else 'NOT MET'} (required {a.threshold:+.0f}%)")

    if a.offer_type == "b2b":
        target_local = o_net_eur / a.current_to_eur
        lo, hi = 0.0, 3_000_000.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if cur.employee_net(mid)[0] < target_local: lo = mid
            else: hi = mid
        print(f"EQUIV    this freelance net equals an employee gross of ~{hi:,.0f} {cur_ccy} in {a.country.upper()}")
        print("NOTE     Freelance net is BEFORE valuing lost protections (unemployment, sick pay, paid vacation, pension accrual; in the US also employer health insurance and 401(k) match). Cover that in the verdict.")
    if off_cc != a.country.upper():
        print("NOTE     Cross-country comparison: living costs, healthcare, pensions and exchange-rate risk are not captured by net pay.")
    print("NOTE     Approximate, annual basis, single filer. 12 vs 14 payments changes cash flow, not annual net.")


if __name__ == "__main__":
    main()
