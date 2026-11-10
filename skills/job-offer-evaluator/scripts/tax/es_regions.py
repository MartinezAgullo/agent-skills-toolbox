"""Spanish autonomous communities: turn free text ("Cataluña", "Valencia"...) into a region record.

Fiscal residence decides which community's IRPF scale applies: the community where the taxpayer
lives on 31 December, NOT where the job is located or where the employer is registered.

Region data lives in data/tax_es_regions.json (one object per community, each with its aliases);
communities that cannot be modelled (foral regimes, Ceuta, Melilla) live in data/tax_es.json under
`regions_not_modelled`. This module only matches names; it holds no tax numbers.
"""
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REGIONS_DATA = Path(__file__).resolve().parents[2] / "data" / "tax_es_regions.json"

# Resolution outcomes.
MODELLED = "modelled"            # we have an official scale for it
NOT_MODELLED = "not_modelled"    # known, but outside the model (foral regimes, Ceuta, Melilla)
UNKNOWN = "unknown"              # a name we have no data for (any other community, or a typo)
UNSPECIFIED = "unspecified"      # the caller gave no region at all


@dataclass(frozen=True)
class RegionChoice:
    """Result of matching a user-supplied region name."""
    requested: Optional[str]     # the name exactly as given, or None
    status: str                  # one of the constants above
    region_id: Optional[str]     # e.g. "madrid"; None unless status is MODELLED
    data: Optional[dict]         # the region record from tax_es_regions.json; None unless MODELLED
    reason: Optional[str] = None  # why it is not modelled (NOT_MODELLED only)


def load_regions(path: Path = REGIONS_DATA) -> dict:
    """Read the per-community data file."""
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(name: str) -> str:
    """Lowercase, strip accents and punctuation: 'Cataluña' -> 'cataluna', 'C. Valenciana' -> 'c valenciana'."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def resolve(name: Optional[str], regions: dict, not_modelled: list) -> RegionChoice:
    """Match `name` against region ids, names and aliases, then against the not-modelled list."""
    if name is None or not name.strip():
        return RegionChoice(None, UNSPECIFIED, None, None)
    key = normalize(name)
    for region_id, record in regions.items():
        names = [region_id.replace("_", " "), record["name"], *record.get("aliases", [])]
        if key in {normalize(n) for n in names}:
            return RegionChoice(name, MODELLED, region_id, record)
    for entry in not_modelled:
        if key in {normalize(n) for n in [entry["id"].replace("_", " "), entry["name"], *entry.get("aliases", [])]}:
            return RegionChoice(name, NOT_MODELLED, None, None, entry["reason"])
    return RegionChoice(name, UNKNOWN, None, None)


def fallback_warning(choice: RegionChoice) -> Optional[str]:
    """Visible notice when the combined state-scale approximation is used instead of a real regional scale."""
    tail = ("Se usa la escala estatal sin los detalles específicos de la comunidad (tramos, tipos y deducciones "
            "autonómicas); el resultado es una aproximación.")
    if choice.status == MODELLED:
        return None
    if choice.status == UNSPECIFIED:
        return f"No se ha indicado la comunidad de residencia fiscal (31 de diciembre). {tail}"
    if choice.status == NOT_MODELLED:
        return f"La comunidad '{choice.requested}' no está modelada ({choice.reason}). {tail}"
    return f"No hay datos de la comunidad '{choice.requested}'. {tail}"
