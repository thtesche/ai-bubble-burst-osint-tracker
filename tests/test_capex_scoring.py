"""Unit tests for MarketDataFetcher CapEx/FCF scoring logic."""
import os
import sys
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.fetchers.market import MarketDataFetcher


@pytest.fixture
def fetcher():
    """Create a MarketDataFetcher instance with no real tickers."""
    return MarketDataFetcher(tickers=[])


# ── Szenario 1: CapEx wächst schneller als FCF → Hohes Bubble-Risiko ─────────


class TestScenarioBubbleRisk:
    """CapEx-Wachstum > FCF-Wachstum → Score in die Nähe von 1.0."""

    @pytest.mark.parametrize(
        "capex_values,fcf_values,expected_min,description",
        [
            (
                [10.0, 12.0, 15.0, 18.0],   # ~20% pro Quartal
                [-100.0, -102.0, -105.0, -108.0],  # ~2% pro Quartal
                0.80,
                "CapEx 20% vs FCF 2%",
            ),
            (
                [10.0, 15.0, 20.0, 25.0],    # 50% pro Quartal
                [-100.0, -101.0, -102.0, -103.0],  # ~1% pro Quartal
                0.95,
                "CapEx 50% vs FCF 1%",
            ),
        ],
    )
    def test_capex_grows_faster_than_fcf(self, fetcher, capex_values, fcf_values,
                                          expected_min, description):
        capex_data = {
            "MSFT": {
                "quarterly_capex": {
                    "2025-Q1": capex_values[0],
                    "2025-Q2": capex_values[1],
                    "2025-Q3": capex_values[2],
                    "2025-Q4": capex_values[3],
                },
                "quarterly_free_cash_flow": {
                    "2025-Q1": fcf_values[0],
                    "2025-Q2": fcf_values[1],
                    "2025-Q3": fcf_values[2],
                    "2025-Q4": fcf_values[3],
                },
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        assert expected_min <= score <= 1.0, (
            f"{description}: Expected >= {expected_min}, got {score:.4f}"
        )


# ── Szenario 2: FCF wächst schneller als CapEx → Gesundes Wachstum (niedrig) ─


class TestScenarioHealthyGrowth:
    """FCF-Wachstum > CapEx-Wachstum → Score in die Nähe von 0.0."""

    @pytest.mark.parametrize(
        "capex_values,fcf_values,expected_max,description",
        [
            (
                [10.0, 11.0, 11.5, 12.0],    # ~8% pro Quartal
                [50.0, 60.0, 75.0, 90.0],     # ~26% pro Quartal (absolute Werte)
                0.30,
                "FCF 26% vs CapEx 8%",
            ),
            (
                [10.0, 10.0, 10.0, 10.0],    # 0% Wachstum
                [50.0, 60.0, 75.0, 95.0],     # 28% pro Quartal (absolute Werte)
                0.25,
                "FCF 28% vs CapEx 0%",
            ),
        ],
    )
    def test_fcf_grows_faster_than_capex(self, fetcher, capex_values, fcf_values,
                                          expected_max, description):
        capex_data = {
            "AAPL": {
                "quarterly_capex": {
                    "2025-Q1": capex_values[0],
                    "2025-Q2": capex_values[1],
                    "2025-Q3": capex_values[2],
                    "2025-Q4": capex_values[3],
                },
                "quarterly_free_cash_flow": {
                    "2025-Q1": fcf_values[0],
                    "2025-Q2": fcf_values[1],
                    "2025-Q3": fcf_values[2],
                    "2025-Q4": fcf_values[3],
                },
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        assert 0.0 <= score <= expected_max, (
            f"{description}: Expected <= {expected_max}, got {score:.4f}"
        )


# ── Szenario 3: Kein FCF → Fallback auf alte CapEx-Logik ─────────────────────


class TestScenarioNoFCF:
    """Fehlt quarterly_free_cash_flow, wird alte Logik verwendet."""

    def test_capex_only_high_growth(self, fetcher):
        """Starke CapEx-Steigerung ohne FCF → Score > 0.5."""
        capex_data = {
            "TSLA": {
                "quarterly_capex": {
                    "2025-Q1": 10.0,
                    "2025-Q2": 14.0,
                    "2025-Q3": 18.0,
                    "2025-Q4": 22.0,
                },
                # KEIN quarterly_free_cash_flow
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        assert score > 0.5, (
            f"Expected >0.5 (CapEx-only fallback with growth), got {score:.4f}"
        )

    def test_capex_only_stable(self, fetcher):
        """Stabiles CapEx ohne FCF → Score nahe 0.5."""
        capex_data = {
            "KO": {
                "quarterly_capex": {
                    "2025-Q1": 10.0,
                    "2025-Q2": 10.0,
                    "2025-Q3": 10.5,
                    "2025-Q4": 10.0,
                },
                # KEIN quarterly_free_cash_flow
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        assert 0.4 <= score <= 0.6, (
            f"Expected ~0.5 (stable CapEx-only), got {score:.4f}"
        )


# ── Szenario 4: Leerer Input / Kein Daten ─────────────────────────────────────


class TestScenarioNoData:
    """Fehlende Daten → Neutral (0.5)."""

    def test_empty_dict(self, fetcher):
        assert fetcher.calculate_capex_score({}) == 0.5

    def test_no_capex_no_fcf(self, fetcher):
        """Weder CapEx noch FCF → 0.5."""
        capex_data = {
            "UNKNOWN": {
                "quarterly_capex": {},
            },
        }
        assert fetcher.calculate_capex_score(capex_data) == 0.5

    def test_no_capex_only_fcf(self, fetcher):
        """Nur FCF, kein CapEx → Neutral 0.5."""
        capex_data = {
            "GOOGL": {
                "quarterly_free_cash_flow": {
                    "2025-Q1": -50.0,
                    "2025-Q2": -60.0,
                    "2025-Q3": -70.0,
                    "2025-Q4": -80.0,
                },
            },
        }
        assert fetcher.calculate_capex_score(capex_data) == 0.5

    def test_no_data_at_all(self, fetcher):
        """Komplett leere Daten → 0.5."""
        capex_data = {"ORCL": {}}
        assert fetcher.calculate_capex_score(capex_data) == 0.5


# ── Szenario 5: Beide gleich stark wachsend → Neutral (Score ~0.5) ────────────


class TestScenarioEqualGrowth:
    """Beide Wachstumsraten gleich → Score ~0.5."""

    def test_identical_growth_rates(self, fetcher):
        """CapEx und FCF wachsen um exakt dieselbe Rate → Score nahe 0.5."""
        capex_data = {
            "AMZN": {
                "quarterly_capex": {
                    "2025-Q1": 10.0,
                    "2025-Q2": 12.0,
                    "2025-Q3": 14.4,
                    "2025-Q4": 17.28,  # 20% pro Quartal
                },
                "quarterly_free_cash_flow": {
                    "2025-Q1": -100.0,
                    "2025-Q2": -120.0,
                    "2025-Q3": -144.0,
                    "2025-Q4": -172.8,  # auch 20% pro Quartal
                },
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        assert 0.45 <= score <= 0.55, (
            f"Expected ~0.5 (equal growth), got {score:.4f}"
        )


# ── Szenario 6: CapEx sinkt, FCF wächst → Sehr niedriges Risiko ───────────────


class TestScenarioDecliningCapEx:
    """CapEx nimmt ab, FCF wächst → Score < 0.3."""

    def test_both_declining(self, fetcher):
        """Beide Cash-Ströme schrumpfen, aber CapEx sinkt viel schneller →
           Score sehr niedrig (gesundes Wachstum)."""
        capex_data = {
            "IBM": {
                "quarterly_capex": {
                    "2025-Q1": 20.0,
                    "2025-Q2": 18.0,
                    "2025-Q3": 16.0,
                    "2025-Q4": 14.0,  # CapEx sinkt ~−10%/Q
                },
                "quarterly_free_cash_flow": {
                    "2025-Q1": 80.0,
                    "2025-Q2": 82.0,
                    "2025-Q3": 84.0,
                    "2025-Q4": 86.0,  # FCF wächst ~2.5%/Q
                },
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        # CapEx sinkt schneller als FCF → diff < 0 → Score → 0.0
        assert score == 0.0, (
            f"Expected 0.0 (CapEx dropping faster than FCF), got {score:.4f}"
        )

    def test_capex_declining_fcf_growing(self, fetcher):
        """CapEx nimmt ab, FCF wächst stark → Score sehr niedrig."""
        capex_data = {
            "META": {
                "quarterly_capex": {
                    "2025-Q1": 20.0,
                    "2025-Q2": 15.0,
                    "2025-Q3": 12.0,
                    "2025-Q4": 10.0,  # CapEx sinkt
                },
                "quarterly_free_cash_flow": {
                    "2025-Q1": 80.0,
                    "2025-Q2": 90.0,
                    "2025-Q3": 100.0,
                    "2025-Q4": 110.0,  # FCF wächst
                },
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        assert score < 0.3, (
            f"Expected <0.3 (declining CapEx + growing FCF), got {score:.4f}"
        )


# ── Szenario 7: Multi-Ticker → Durchschnittsbildung ────────────────────────────


class TestScenarioMultiTicker:
    """Mehrere Ticker werden gemittelt."""

    def test_mixed_tickers_average(self, fetcher):
        """Ein Bubble-Ticker + ein gesunder Ticker → Score mittelt sich."""
        capex_data = {
            "MSFT": {
                "quarterly_capex": {
                    "2025-Q1": 10.0,
                    "2025-Q2": 12.0,
                    "2025-Q3": 15.0,
                    "2025-Q4": 18.0,
                },
                "quarterly_free_cash_flow": {
                    "2025-Q1": -100.0,
                    "2025-Q2": -102.0,
                    "2025-Q3": -105.0,
                    "2025-Q4": -108.0,
                },
            },
            "AAPL": {
                "quarterly_capex": {
                    "2025-Q1": 10.0,
                    "2025-Q2": 11.0,
                    "2025-Q3": 11.5,
                    "2025-Q4": 12.0,
                },
                "quarterly_free_cash_flow": {
                    "2025-Q1": -50.0,
                    "2025-Q2": -60.0,
                    "2025-Q3": -75.0,
                    "2025-Q4": -90.0,
                },
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        # Hochriskant (MSFT) + Gesund (AAPL) gemittelt → ~0.5
        assert 0.4 < score < 0.6, (
            f"Expected ~0.5 (average of high+low), got {score:.4f}"
        )

    def test_single_ticker(self, fetcher):
        """Einzelner Ticker wird korrekt berechnet."""
        capex_data = {
            "NVDA": {
                "quarterly_capex": {
                    "2025-Q1": 5.0,
                    "2025-Q2": 6.0,
                    "2025-Q3": 7.0,
                    "2025-Q4": 8.0,
                },
                "quarterly_free_cash_flow": {
                    "2025-Q1": -30.0,
                    "2025-Q2": -40.0,
                    "2025-Q3": -55.0,
                    "2025-Q4": -70.0,
                },
            },
        }
        score = fetcher.calculate_capex_score(capex_data)
        # FCF wächst stark (>50%), CapEx ~15% → Score niedrig
        assert 0.0 <= score <= 0.35, (
            f"Expected <0.35 (healthy), got {score:.4f}"
        )


# ── Test für _compute_avg_growth (Hilfsfunktion) ──────────────────────────────


class TestComputeAvgGrowth:
    """Unit tests für die statische Hilfsfunktion."""

    def test_positive_growth(self):
        values = [10.0, 12.0, 15.0, 18.0]
        result = MarketDataFetcher._compute_avg_growth(values)
        assert result is not None
        assert 0.15 < result < 0.25, f"Expected ~0.2, got {result:.4f}"

    def test_negative_growth(self):
        values = [20.0, 15.0, 12.0, 10.0]
        result = MarketDataFetcher._compute_avg_growth(values)
        assert result is not None
        assert result < 0, f"Expected negative growth, got {result:.4f}"

    def test_stable_values(self):
        values = [10.0, 10.0, 10.0, 10.0]
        result = MarketDataFetcher._compute_avg_growth(values)
        assert result is not None
        assert abs(result) < 0.05, f"Expected ~0 (stable), got {result:.4f}"

    def test_single_value_returns_none(self):
        assert MarketDataFetcher._compute_avg_growth([10.0]) is None

    def test_empty_list_returns_none(self):
        assert MarketDataFetcher._compute_avg_growth([]) is None

    def test_with_zeros(self):
        """Werte enthalten Null → trotzdem berechenbar."""
        values = [0.0, 10.0, 12.0, 15.0]
        result = MarketDataFetcher._compute_avg_growth(values)
        assert result is not None  # Erste Änderung (0→10) wird übergangen, Rest berechnet
