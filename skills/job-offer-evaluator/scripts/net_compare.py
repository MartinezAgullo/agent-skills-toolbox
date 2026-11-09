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

TERMINOLOGY (full glossary: references/terminology.md)
  The tax maths knows exactly two statuses:
    employee       an employer withholds tax and pays your social security (Spain: cuenta ajena; US: W-2).
                   EOR / umbrella arrangements are also `employee`.
    self_employed  you invoice and pay your own social security and income tax
                   (Spain: autonomo, RETA; US: 1099 / sole proprietor).
  "freelance", "contractor", "B2B", "autonomo" and "1099" are all NAMES for `self_employed`. They are accepted
  as input aliases, but the output always says "self-employed" plus the country's own label.
  Not modelled: working through your own company (Spain: SL; US: LLC/S-corp), which taxes differently.
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tax as taxmods


# Every word a recruiter or the user may use, mapped to one of the two statuses the tax modules understand.
STATUS_ALIASES = {
    "employee": "employee", "w2": "employee", "salaried": "employee", "eor": "employee",
    "self_employed": "self_employed", "self-employed": "self_employed", "b2b": "self_employed",
    "freelance": "self_employed", "contractor": "self_employed", "autonomo": "self_employed",
    "autónomo": "self_employed", "1099": "self_employed",
}


def parse_status(value: str) -> str:
    """argparse type: turn any accepted alias into 'employee' or 'self_employed'."""
    try:
        return STATUS_ALIASES[value.strip().lower()]
    except KeyError:
        raise argparse.ArgumentTypeError(
            f"unknown contract type '{value}'. Use employee or self_employed (aliases: {', '.join(sorted(STATUS_ALIASES))})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--country", default="ES", help="tax module for the CURRENT job (ES, US)")
    p.add_argument("--offer-country", default=None, help="tax module for the OFFER (default: same as --country)")
    p.add_argument("--current-gross", type=float, required=True, help="current annual gross incl. expected variable")
    p.add_argument("--current-contract", type=parse_status, default="employee", help="employee | self_employed (aliases: autonomo, freelance, b2b, 1099, w2...)")
    p.add_argument("--current-expenses", type=float, default=0, help="current yearly business costs (only if current contract is self_employed)")
    p.add_argument("--current-to-eur", type=float, default=1.0, help="current country currency -> EUR")
    p.add_argument("--current-benefits", type=float, default=0, help="EUR/yr value of current non-cash benefits")
    p.add_argument("--current-extra-costs", type=float, default=0, help="EUR/yr current out-of-pocket work costs")
    p.add_argument("--offer-type", type=parse_status, required=True, help="employee | self_employed (aliases: b2b, freelance, contractor, autonomo, 1099, w2...)")
    p.add_argument("--offer-gross", type=float, help="employee offers: annual gross, offer-country currency")
    p.add_argument("--hourly", type=float, help="self_employed offers: hourly rate in the PAY currency")
    p.add_argument("--fx", type=float, default=1.0, help="pay currency -> offer-country currency")
    p.add_argument("--to-eur", type=float, default=1.0, help="offer-country currency -> EUR")
    p.add_argument("--hours", type=float, default=1720, help="self_employed offers: billable hours per year")
    p.add_argument("--expenses", type=float, default=1500, help="self_employed offers: yearly business costs (gestor, self-paid health insurance...), offer-country currency")
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
    cur_lbl = getattr(cur, "self_employed_label", "self-employed")
    off_lbl = getattr(off, "self_employed_label", "self-employed")
    if a.current_contract == "employee":
        net_l, soc, tax = cur.employee_net(a.current_gross)
        print(f"CURRENT [{a.country.upper()}, {cur_ccy}, employee]  gross {a.current_gross:,.0f} | social/payroll {soc:,.0f} | income tax {tax:,.0f} | NET {net_l:,.0f}")
    else:
        net_l, soc, tax = cur.self_employed_net(a.current_gross, a.current_expenses)
        print(f"CURRENT [{a.country.upper()}, {cur_ccy}, self-employed: {cur_lbl}]  revenue {a.current_gross:,.0f} | social {soc:,.0f} | income tax {tax:,.0f} | NET {net_l:,.0f}")
    cur_eff = net_l * a.current_to_eur + a.current_benefits - a.current_extra_costs
    print(f"         effective EUR (net + benefits - extra costs): {cur_eff:,.0f}/yr = {cur_eff/12:,.0f}/mo")

    # offer
    if a.offer_type == "self_employed":
        rev = a.hourly * a.fx * a.hours * (1 - a.unpaid_gap_months / 12)
        o_net, o_soc, o_tax = off.self_employed_net(rev, a.expenses)
        print(f"OFFER   [{off_cc}, {off_ccy}, self-employed: {off_lbl}]  revenue {rev:,.0f} | costs {a.expenses:,.0f} | social/SE tax {o_soc:,.0f} | income tax {o_tax:,.0f} | NET {o_net:,.0f}")
    else:
        o_net, o_soc, o_tax = off.employee_net(a.offer_gross)
        print(f"OFFER   [{off_cc}, {off_ccy}, employee]  gross {a.offer_gross:,.0f} | social/payroll {o_soc:,.0f} | income tax {o_tax:,.0f} | NET {o_net:,.0f}")
    o_net_eur = o_net * a.to_eur
    off_eff = o_net_eur + a.offer_benefits - a.offer_extra_costs
    print(f"         effective EUR (net + benefits - extra costs): {off_eff:,.0f}/yr = {off_eff/12:,.0f}/mo")

    diff = off_eff - cur_eff
    pct = diff / cur_eff * 100
    print(f"DELTA    {diff:+,.0f} EUR/yr effective net ({pct:+.1f}%), {diff/12:+,.0f} EUR/mo")
    if a.threshold is not None:
        print(f"THRESHOLD {'MET' if pct >= a.threshold else 'NOT MET'} (required {a.threshold:+.0f}%)")

    if a.offer_type == "self_employed":
        target_local = o_net_eur / a.current_to_eur
        lo, hi = 0.0, 3_000_000.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if cur.employee_net(mid)[0] < target_local: lo = mid
            else: hi = mid
        print(f"EQUIV    this self-employed net equals an employee gross of ~{hi:,.0f} {cur_ccy} in {a.country.upper()}")
        print("NOTE     Self-employed net is BEFORE valuing lost protections (unemployment, sick pay, paid vacation, pension accrual; in the US also employer health insurance and 401(k) match). Cover that in the verdict.")
    if off_cc != a.country.upper():
        print("NOTE     Cross-country comparison: living costs, healthcare, pensions and exchange-rate risk are not captured by net pay.")
    print("NOTE     Approximate, annual basis, single filer. 12 vs 14 payments changes cash flow, not annual net.")


if __name__ == "__main__":
    main()
