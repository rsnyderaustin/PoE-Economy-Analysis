from datetime import datetime
from sqlalchemy import String, DateTime, Float, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column, Mapped

from src.market_item_analysis.database.base_model import Base


class TrainingDataModel(Base):
    __tablename__ = 'training_data'

    id: Mapped[int] = mapped_column(primary_key=True)

    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    indexed_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    price_currency: Mapped[str] = mapped_column(String(100), nullable=False)
    price_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    gold_cost: Mapped[float] = mapped_column(Float, nullable=False)
    ilvl: Mapped[int] = mapped_column(Integer, nullable=False)
    rarity: Mapped[str] = mapped_column(String(10), nullable=False)
    result_object: Mapped[dict] = mapped_column(JSONB, nullable=False)



