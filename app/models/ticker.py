from typing import List
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models.base import BaseModel
from datetime import datetime, timezone


class Ticker(BaseModel):
    __tablename__ = 'ticker'

    symbol: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False, index=True, unique=True)
    exchange: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False)
    instrument_token: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, unique=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(200), nullable=False, index=True)
    last_price: so.Mapped[float] = so.mapped_column(sa.Float, default=0.0, nullable=False)
    last_updated: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

    # Relationships
    trades: so.Mapped[List["Trade"]] = so.relationship(back_populates='ticker')

    def __repr__(self):
        return f'<Ticker {self.symbol}>'

