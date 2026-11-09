# Adding a country tax module

Spain (`scripts/tax/es.py`, `data/tax_es.json`) and the United States (`scripts/tax/us.py`, `data/tax_us.json`) exist. For any other country the skill estimates net manually and labels it a rough estimate. If the user gets repeated offers from one country, build a module:

1. Copy `data/tax_es.json` to `data/tax_<cc>.json` and fill it from official sources (income tax bands, employee and self-employed social security, caps, standard deductions). Record `tax_year`, `verified_on`, `sources`, and set `verified_by` honestly.
2. Copy `scripts/tax/es.py` to `scripts/tax/<cc>.py`, keep the `Module` class and the interface in `scripts/tax/base.py` (`employee_net`, `self_employed_net`, `staleness`). Regional variation (canton, state, community) goes in the `regional_shift` constructor argument or in the data file.
3. Test with `python3 scripts/net_compare.py --country <CC> ...` against a known payslip before trusting it.

Keep tax rules in the data file, not in code, so the yearly refresh only touches JSON.

Each module sets a class attribute `currency` (e.g. "EUR", "USD"). `net_compare.py` converts offer-country net into EUR with `--to-eur`, so the module itself never deals with FX.
