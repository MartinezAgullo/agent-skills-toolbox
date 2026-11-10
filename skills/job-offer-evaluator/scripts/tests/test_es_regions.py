"""Checks for the Spanish regional IRPF scales. Run: python3 -m unittest discover -s scripts/tests -v

Expected quotas below are literals, derived by hand from the OFFICIAL 'cuota integra' columns of each
published scale (table lookup: cuota at the bracket floor + rate * excess), then net of the personal
minimum. They do not go through the rates stored in data/tax_es_regions.json, so a transcription slip
in the JSON shows up here. Sources are listed per region in that JSON file.

Quota = IRPF on a taxable base (base liquidable general): state part + autonomic part, each minus the
tax its personal minimum would generate (state 5,550; autonomic 5,956.65 Madrid, 5,790 Andalucia,
6,105 Comunitat Valenciana, 5,550 Cataluña and Cantabria).
"""
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from tax import es, es_regions  # noqa: E402

BASES = (20_000, 46_000, 80_000)
STATE_QUOTA = {20_000: 1561.50, 46_000: 5833.50, 80_000: 12923.50}   # art. 63 Ley 35/2006, official cuota column
# region -> {base: (autonomic quota, total quota)}
EXPECTED = {
    "madrid":               {20_000: (1360.62, 2922.12), 46_000: (5175.04, 11008.54), 80_000: (11794.10, 24717.60)},
    "cataluna":             {20_000: (1597.75, 3159.25), 46_000: (6077.75, 11911.25), 80_000: (13212.75, 26136.25)},
    "comunitat_valenciana": {20_000: (1454.76, 3016.26), 46_000: (5624.76, 11458.26), 80_000: (13506.76, 26430.26)},
    "andalucia":            {20_000: (1524.95, 3086.45), 46_000: (5769.95, 11603.45), 80_000: (12859.95, 25783.45)},
    "cantabria":            {20_000: (1403.25, 2964.75), 46_000: (5516.25, 11349.75), 80_000: (12536.25, 25459.75)},
}
FALLBACK_TAIL = "el resultado es una aproximación"


class RegionalQuotas(unittest.TestCase):
    def test_total_quota_matches_official_tables(self):
        for region, by_base in EXPECTED.items():
            for base, (regional, total) in by_base.items():
                with self.subTest(region=region, base=base):
                    state_part, regional_part = es.Module(region=region).irpf_breakdown(base)
                    self.assertAlmostEqual(state_part, STATE_QUOTA[base], delta=0.01)
                    self.assertAlmostEqual(regional_part, regional, delta=0.01)
                    self.assertAlmostEqual(state_part + regional_part, total, delta=0.01)

    def test_regions_are_distinct_from_each_other(self):
        totals = {r: es.Module(region=r).irpf_breakdown(46_000)[1] for r in EXPECTED}
        self.assertEqual(len(set(round(v, 2) for v in totals.values())), len(EXPECTED))


class Fallback(unittest.TestCase):
    def assert_state_scale_fallback(self, region, expected_start):
        module = es.Module(region=region)
        for base in BASES:
            state_part, regional_part = module.irpf_breakdown(base)
            self.assertAlmostEqual(regional_part, state_part, places=6)   # combined scale = 2 x state
        warnings = module.approximation_warnings()
        self.assertEqual(len(warnings), 1)
        self.assertTrue(warnings[0].startswith(expected_start), warnings[0])
        self.assertIn(FALLBACK_TAIL, warnings[0])

    def test_unknown_community(self):
        self.assert_state_scale_fallback("Galicia", "No hay datos de la comunidad 'Galicia'.")

    def test_no_region_given(self):
        self.assert_state_scale_fallback(None, "No se ha indicado la comunidad de residencia fiscal")

    def test_foral_and_special_cities(self):
        for name in ("País Vasco", "Navarra", "Ceuta", "Melilla", "Euskadi"):
            with self.subTest(name=name):
                self.assert_state_scale_fallback(name, f"La comunidad '{name}' no está modelada")

    def test_modelled_region_has_no_fallback_warning(self):
        self.assertEqual(es.Module(region="madrid").approximation_warnings(), [])

    def test_no_region_matches_previous_combined_scale_results(self):
        """Without a region the old numbers (computed before regional scales existed) must not change."""
        module = es.Module()
        self.assertEqual([round(x) for x in module.employee_net(46_000)], [33_189, 2_990, 9_821])
        self.assertEqual([round(x) for x in module.employee_net(60_000)], [41_436, 3_900, 14_664])
        # the manual shift must keep working exactly as before (pp added to every rate of the combined scale)
        self.assertEqual([round(x) for x in es.Module(-0.015).employee_net(46_000)], [33_721, 2_990, 9_289])
        self.assertEqual([round(x) for x in es.Module(0.01).self_employed_net(20_000, 2_000)], [12_688, 3_632, 1_680])


class Resolution(unittest.TestCase):
    ALIASES = {
        "madrid": ["Madrid", "Comunidad de Madrid", "MADRID"],
        "cataluna": ["Cataluña", "Catalunya", "cataluna", "Catalonia"],
        "comunitat_valenciana": ["Comunidad Valenciana", "Comunitat Valenciana", "Valencia", "comunitat_valenciana"],
        "andalucia": ["Andalucía", "andalucia"],
        "cantabria": ["Cantabria", " cantabria "],
    }

    def test_aliases(self):
        for region_id, names in self.ALIASES.items():
            for name in names:
                with self.subTest(name=name):
                    self.assertEqual(es.Module(region=name).choice.region_id, region_id)


class DataIntegrity(unittest.TestCase):
    def test_region_records(self):
        for region_id, rec in es_regions.load_regions().items():
            with self.subTest(region=region_id):
                for key in ("name", "tax_year", "scale", "verified_on", "verified_by", "sources", "unverified", "notes"):
                    self.assertIn(key, rec)
                tops = [t for t, _ in rec["scale"]]
                self.assertIsNone(tops[-1])
                self.assertEqual(tops[:-1], sorted(tops[:-1]))
                rates = [r for _, r in rec["scale"]]
                self.assertEqual(rates, sorted(rates))
                self.assertTrue(all(0 < r < 0.35 for r in rates))
                self.assertTrue(all(s["url"].startswith("https://") for s in rec["sources"]))

    def test_state_and_regional_data_are_separate(self):
        self.assertNotIn("irpf_scale", es.Module().params)   # no combined scale stored anywhere
        self.assertEqual(es.Module().params["irpf_state_scale"][-1], [None, 0.245])


class Staleness(unittest.TestCase):
    def test_unverified_item_of_selected_region_is_reported(self):
        self.assertIn("still unverified", es.Module(region="Valencia").staleness(date(2026, 11, 9)))
        self.assertNotIn("Comunitat Valenciana", es.Module(region="Madrid").staleness(date(2026, 11, 9)) or "")

    def test_region_data_older_than_calendar_year(self):
        self.assertIn("Madrid IRPF scale is for 2026", es.Module(region="madrid").staleness(date(2027, 1, 5)))


class CommandLine(unittest.TestCase):
    def run_cli(self, *args):
        cmd = [sys.executable, "-I", str(SCRIPTS / "net_compare.py"), "--current-gross", "46000",
               "--offer-type", "employee", "--offer-gross", "60000", *args]
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout

    def test_warning_is_in_output_for_unknown_and_missing_region(self):
        self.assertIn("No hay datos de la comunidad 'Galicia'", self.run_cli("--region", "Galicia"))
        self.assertIn("No se ha indicado la comunidad de residencia fiscal", self.run_cli())

    def test_no_warning_when_both_regions_are_modelled(self):
        out = self.run_cli("--region", "madrid", "--offer-region", "Cataluña")
        self.assertNotIn("aproximación", out)

    def test_offer_region_defaults_to_current_region(self):
        a = self.run_cli("--region", "madrid")
        b = self.run_cli("--region", "madrid", "--offer-region", "madrid")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
