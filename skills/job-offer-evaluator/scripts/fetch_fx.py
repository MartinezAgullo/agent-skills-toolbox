#!/usr/bin/env python3
"""Print the current FX rate (ECB reference via frankfurter.dev). Usage: fetch_fx.py USD [EUR]"""
import json, sys, urllib.request

base = sys.argv[1].upper()
quote = sys.argv[2].upper() if len(sys.argv) > 2 else "EUR"
if base == quote:
    print(f"1.0 (same currency)"); sys.exit(0)
try:
    with urllib.request.urlopen(f"https://api.frankfurter.dev/v1/latest?base={base}&symbols={quote}", timeout=10) as r:
        d = json.load(r)
    print(f"{d['rates'][quote]} ({base}->{quote}, ECB {d['date']})")
except Exception as e:
    print(f"FX lookup failed ({e}). Ask the user for the rate.", file=sys.stderr); sys.exit(1)
