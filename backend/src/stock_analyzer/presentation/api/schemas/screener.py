"""Screener and similar-setup response models."""

from dataclasses import asdict
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from stock_analyzer.application.use_cases.screener.queries import AnalogSummary, ScreenRow
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.presentation.api.schemas.stocks import PredictionResponse, StockResponse

STOCK_EXAMPLE: dict[str, JsonValue] = {
    "symbol": "INFY",
    "name": "Infosys Ltd",
    "exchange": "NSE",
    "market": "IN",
    "sector": "Information Technology",
    "currency": "INR",
    "is_synthetic": True,
}


class ScreenRowResponse(BaseModel):
    """One ranked screener result."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "stock": STOCK_EXAMPLE,
                    "prediction": {
                        "category": "50D",
                        "calendar_days": 50,
                        "as_of": "2026-10-30",
                        "p10_pct": -6.2,
                        "p50_pct": 4.1,
                        "p90_pct": 15.3,
                        "prob_up": 0.61,
                        "prob_hit": {"5": 0.48, "10": 0.31, "20": 0.12},
                        "cagr_p50_pct": None,
                        "model_version": "baseline-empirical-v1",
                    },
                    "probability": 0.31,
                    "probability_max": 0.12,
                    "quality": 7,
                }
            ]
        }
    )

    stock: StockResponse
    prediction: PredictionResponse
    probability: float | None = Field(description="Chance of the requested target before the stop")
    probability_max: float | None = Field(description="Chance of the upper end of the range")
    quality: int | None = Field(description="0-10 quality score (Q67)")

    @classmethod
    def from_domain(cls, row: ScreenRow) -> "ScreenRowResponse":
        """Map a screener row."""
        return cls(
            stock=StockResponse.from_domain(row.stock),
            prediction=PredictionResponse.from_domain(row.prediction),
            probability=float(row.probability) if row.probability is not None else None,
            probability_max=(
                float(row.probability_max) if row.probability_max is not None else None
            ),
            quality=row.quality,
        )


class AnalogCaseResponse(BaseModel):
    """A similar past setup and its outcome."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "symbol": "TCS",
                    "as_of": "2024-03-04",
                    "similarity": 0.987,
                    "return_pct": 12.4,
                    "is_stopped": False,
                }
            ]
        }
    )

    symbol: str
    as_of: date
    similarity: float
    return_pct: float
    is_stopped: bool


class AnalogSummaryResponse(BaseModel):
    """Outcome summary of the most similar past setups."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "symbol": "INFY",
                    "category": "1Y",
                    "as_of": "2026-10-30",
                    "median_return_pct": 9.8,
                    "share_up": 0.65,
                    "hit_rates": {"5": 0.55, "10": 0.45, "20": 0.2},
                    "cases": [
                        {
                            "symbol": "TCS",
                            "as_of": "2024-03-04",
                            "similarity": 0.987,
                            "return_pct": 12.4,
                            "is_stopped": False,
                        }
                    ],
                }
            ]
        }
    )

    symbol: str
    category: HoldingCategory
    as_of: date | None
    median_return_pct: float | None
    share_up: float | None
    hit_rates: dict[str, float]
    cases: list[AnalogCaseResponse]

    @classmethod
    def from_domain(cls, summary: AnalogSummary) -> "AnalogSummaryResponse":
        """Map an analog summary."""
        return cls(
            symbol=summary.symbol,
            category=summary.category,
            as_of=summary.as_of,
            median_return_pct=summary.median_return_pct,
            share_up=summary.share_up,
            hit_rates={str(t): v for t, v in summary.hit_rates.items()},
            cases=[AnalogCaseResponse(**asdict(c)) for c in summary.cases],
        )
