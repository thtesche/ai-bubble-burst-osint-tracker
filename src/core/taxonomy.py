from typing import Dict, List, Optional, Set

# Strukturierte Taxonomie der KI-Wertschöpfungskette
AI_VALUE_CHAIN: Dict[str, Dict[str, object]] = {
    "hyperscalers": {
        "name": "Hyperscaler & Cloud-Anbieter",
        "tickers": ["MSFT", "GOOGL", "AMZN", "META"],
    },
    "compute_hardware": {
        "name": "Rechenkapazität & Beschleuniger (GPUs/CPUs)",
        "tickers": ["NVDA", "AMD", "AVGO", "DELL", "SMCI", "HPE"],
    },
    "memory_storage": {
        "name": "Speicher & Storage (HBM/NAND/HDDs)",
        "tickers": ["MU", "WDC", "STX"],
    },
    "semiconductor_equip": {
        "name": "Halbleiter-Ausrüstung & Foundries",
        "tickers": ["TSM", "ASML", "AMAT", "LRCX", "KLAC"],
    },
    "cooling_thermal": {
        "name": "Kühlung & Thermomanagement",
        "tickers": ["VRT", "TT"],
    },
    "power_grid": {
        "name": "Stromnetz & Elektrotechnische Infrastruktur",
        "tickers": ["ETN", "GEV", "PWR"],
    },
    "networking": {
        "name": "Netzwerk & Interconnects",
        "tickers": ["ANET", "APH", "MRVL"],
    },
    "data_centers": {
        "name": "Rechenzentren & Data Center REITs",
        "tickers": ["EQIX", "DLR"],
    },
    "ai_software": {
        "name": "KI-Software & Applikations-Ebene",
        "tickers": ["PLTR", "CRM", "NOW"],
    },
}


def get_all_tickers(categories: Optional[List[str]] = None) -> List[str]:
    """Liefert eine duplikatfreie, sortierte Liste aller Ticker (oder gefiltert nach Kategorien)."""
    selected: Set[str] = set()
    target_cats = categories if categories is not None else AI_VALUE_CHAIN.keys()

    for cat in target_cats:
        if cat in AI_VALUE_CHAIN:
            selected.update(AI_VALUE_CHAIN[cat]["tickers"])

    return sorted(list(selected))


def get_tickers_by_category() -> Dict[str, List[str]]:
    """Gibt ein Dictionary der Form {'kategorie': ['TICKER1', 'TICKER2']} zurück."""
    return {cat: data["tickers"] for cat, data in AI_VALUE_CHAIN.items()}


# Abwärtskompatibles Standard-Array für bestehenden Code
DEFAULT_TICKERS = get_all_tickers()
