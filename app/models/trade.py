from __future__ import annotations
from typing import List, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from app.models.base import BaseModel
from app.models.utils import TradeStatus, TradeTimeframe, trade_side_enum, \
    trade_type_enum, trade_status_enum, trade_timeframe_enum, trade_eta_enum
from datetime import datetime, timezone

# Many-to-many relationship with tags
trade_tags = sa.Table('trade_tags',
                      db.metadata,
                      sa.Column('trade_id', sa.String(36), sa.ForeignKey('trade.id'), primary_key=True),
                      sa.Column('tag_id', sa.String(36), sa.ForeignKey('tag.id'), primary_key=True))


class Trade(BaseModel):
    __tablename__ = 'trade'

    symbol: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False, index=True)
    side: so.Mapped[str] = so.mapped_column(trade_side_enum, nullable=False)
    type: so.Mapped[str] = so.mapped_column(trade_type_enum, nullable=False)
    status: so.Mapped[str] = so.mapped_column(trade_status_enum, nullable=False, default=TradeStatus.ACTIVE)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False, default="")

    # Price
    entry: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)
    stoploss: so.Mapped[Optional[float]] = so.mapped_column(sa.Float, nullable=True)
    target: so.Mapped[Optional[float]] = so.mapped_column(sa.Float, nullable=True)

    timeframe: so.Mapped[str] = so.mapped_column(trade_timeframe_enum, nullable=False, default=TradeTimeframe.DAY)

    # Score
    score: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True, default=0)

    # Chart Co-ordinates
    entry_x: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True,
                                                              default=lambda: datetime.now(timezone.utc))

    stoploss_x: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True,
                                                                 default=lambda: datetime.now(timezone.utc))

    target_x: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True,
                                                               default=lambda: datetime.now(timezone.utc))

    # ETA
    entry_eta: so.Mapped[Optional[str]] = so.mapped_column(trade_eta_enum, nullable=True)
    stoploss_eta: so.Mapped[Optional[str]] = so.mapped_column(trade_eta_enum, nullable=True)
    target_eta: so.Mapped[Optional[str]] = so.mapped_column(trade_eta_enum, nullable=True)

    # Time
    entry_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True)
    stoploss_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True)
    target_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True)
    edited_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True)
    status_updated_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True)
    updated_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime(timezone=True), nullable=True,
                                                                 default=lambda: datetime.now(timezone.utc))

    # Foreign keys
    user_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey("user.id"), index=True, nullable=False)
    ticker_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey("ticker.id"), index=True, nullable=False)

    # Relationships
    user: so.Mapped["User"] = so.relationship(back_populates="trades")
    ticker: so.Mapped["Ticker"] = so.relationship(back_populates="trades")
    tags: so.Mapped[List["Tag"]] = so.relationship(secondary=trade_tags, back_populates="trades")

    def __repr__(self):

        return f'<Trade {self.symbol} - {self.type} {self.side}>'

    @property
    def last_price(self):
        return self.ticker.last_price

    @property
    def risk_reward_ratio(self):
        if not self.stoploss or not self.target:
            return None
        return round(self.reward_per_unit / self.risk_per_unit, 2)

    @property
    def risk_per_unit(self):
        if not self.stoploss:
            return None
        return abs(self.entry - self.stoploss)

    @property
    def reward_per_unit(self):
        if not self.target:
            return None
        return abs(self.target - self.entry)

