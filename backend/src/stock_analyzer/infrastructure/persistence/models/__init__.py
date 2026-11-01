"""ORM models. Import every model here so Alembic sees the full metadata."""

from stock_analyzer.infrastructure.persistence.models.auth import (
    AuditLogModel,
    InviteCodeModel,
    InviteRedemptionModel,
    LoginRequestModel,
    SessionModel,
    UserModel,
    WatchlistModel,
)
from stock_analyzer.infrastructure.persistence.models.base import Base
from stock_analyzer.infrastructure.persistence.models.fundamentals import (
    CorporateActionModel,
    FundamentalsModel,
)
from stock_analyzer.infrastructure.persistence.models.job import JobRunModel
from stock_analyzer.infrastructure.persistence.models.journal import (
    JournalSettingsModel,
    PlanDailyStatusModel,
    TradePlanModel,
)
from stock_analyzer.infrastructure.persistence.models.market import MarketModel, StockModel
from stock_analyzer.infrastructure.persistence.models.ml import FeatureDailyModel, LabelDailyModel
from stock_analyzer.infrastructure.persistence.models.prediction import (
    ModelVersionModel,
    PredictionModel,
)
from stock_analyzer.infrastructure.persistence.models.price import PriceDailyModel
from stock_analyzer.infrastructure.persistence.models.provider import (
    ProviderAssignmentModel,
    ProviderCredentialModel,
    ProviderModel,
)

__all__ = [
    "AuditLogModel",
    "Base",
    "CorporateActionModel",
    "FeatureDailyModel",
    "FundamentalsModel",
    "InviteCodeModel",
    "InviteRedemptionModel",
    "JobRunModel",
    "JournalSettingsModel",
    "LabelDailyModel",
    "LoginRequestModel",
    "MarketModel",
    "ModelVersionModel",
    "PlanDailyStatusModel",
    "PredictionModel",
    "PriceDailyModel",
    "ProviderAssignmentModel",
    "ProviderCredentialModel",
    "ProviderModel",
    "SessionModel",
    "StockModel",
    "TradePlanModel",
    "UserModel",
    "WatchlistModel",
]
