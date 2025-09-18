from __future__ import annotations
from typing import List, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from app.models.base import BaseModel
from app.models.utils import TradeStatus, TradeTimeframe, trade_side_enum, \
    trade_type_enum, trade_status_enum, trade_timeframe_enum, trade_eta_enum, TradeSide, TradeETA, TradeType
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
        try:
            return round(self.reward_per_unit / self.risk_per_unit, 1)
        except ZeroDivisionError:
            return None

    @property
    def risk_per_unit(self):
        if not self.stoploss:
            return None
        return self.entry - self.stoploss if self.side == TradeSide.BUY else self.stoploss - self.entry

    @property
    def reward_per_unit(self):
        if not self.target:
            return None
        return self.target - self.entry if self.side == TradeSide.BUY else self.entry - self.target

    # Add these methods to your existing Trade model in app/models/trade.py

    @classmethod
    def get_active_trades_for_ticker(cls, ticker_id):
        """Get all active trades for a specific ticker"""
        from app.models.utils import TradeStatus

        return cls.query.filter(
            cls.ticker_id == ticker_id,
            cls.status.in_([TradeStatus.ACTIVE, TradeStatus.ENTRY])
        ).all()

    @classmethod
    def check(self, candle):
        """Check if a trade status should change based on candle data"""

        now = datetime.now(timezone.utc)
        status_changed = False
        candle_high = candle.high
        candle_low = candle.low

        if self.status == TradeStatus.ACTIVE:
            # For ACTIVE trades

            if self.type == TradeType.CROSSING_ABOVE:
                # For CROSSING_ABOVE trades

                if self.side == TradeSide.BUY:
                    # For BUY trades where entry is above last price

                    if self.target and candle_high >= self.target:
                        # Check for Missed Case

                        self.status = TradeStatus.TARGET
                        self.target_at = now
                        status_changed = True

                    elif candle_high >= self.entry:
                        # Check for Entry

                        self.status = TradeStatus.ENTRY
                        self.entry_at = now
                        status_changed = True

                elif self.side == TradeSide.SELL:
                    # For SELL trades where entry is above last price

                    if self.stoploss and candle_high > self.stoploss:
                        # Check for Failed Case

                        self.status = TradeStatus.STOPLOSS
                        self.stoploss_at = now
                        status_changed = True

                    elif candle_high >= self.entry:
                        # Check for Entry

                        self.status = TradeStatus.ENTRY
                        self.entry_at = now
                        status_changed = True

            elif self.type == TradeType.CROSSING_BELOW:
                # For CROSSING_BELOW trades

                if self.side == TradeSide.BUY:
                    # For BUY trades where entry is below last price

                    if self.stoploss and candle_low < self.stoploss:
                        # Check for Failed Case

                        self.status = TradeStatus.STOPLOSS
                        self.stoploss_at = now
                        status_changed = True

                    elif candle_low <= self.entry:
                        # Check for Entry

                        self.status = TradeStatus.ENTRY
                        self.entry_at = now
                        status_changed = True

                elif self.side == TradeSide.SELL:
                    # For SELL trades where entry is below last price

                    if self.target and candle_low <= self.target:
                        # Check for Missed Case

                        self.status = TradeStatus.TARGET
                        self.target_at = now
                        status_changed = True

                    elif candle_low <= self.entry:
                        # Check for Entry

                        self.status = TradeStatus.ENTRY
                        self.entry_at = now
                        status_changed = True

        elif self.status == TradeStatus.ENTRY:
            # For ENTRY trades

            if self.side == TradeSide.BUY:
                # For BUY trades

                # For BUY trades that have hit entry
                if self.stoploss and candle_low < self.stoploss:
                    # Check for Stoploss

                    self.status = TradeStatus.STOPLOSS
                    self.stoploss_at = now
                    status_changed = True

                elif self.target and candle_high >= self.target:
                    # Check for Target

                    self.status = TradeStatus.TARGET
                    self.target_at = now
                    status_changed = True

            elif self.side == TradeSide.SELL:
                # For SELL trades

                if self.stoploss and candle_high > self.stoploss:
                    # Check for Stoploss

                    self.status = TradeStatus.STOPLOSS
                    self.stoploss_at = now
                    status_changed = True

                elif self.target and candle_low <= self.target:
                    # Check for Target

                    self.status = TradeStatus.TARGET
                    self.target_at = now
                    status_changed = True

        if status_changed:
            self.status_updated_at = now
            self.updated_at = now
            db.session.commit()

        return status_changed

    def update_etas(self):
        """Update ETA fields based on current price and trade parameters"""

        current_price = self.last_price

        if not current_price:
            return

        # Update entry ETA
        if self.status == TradeStatus.ACTIVE:
            self.entry_eta = self._calculate_eta(self.entry)
            self.stoploss_eta = None
            self.target_eta = None

        # Update stoploss ETA
        elif self.status == TradeStatus.ENTRY:
            self.entry_eta = None

            if self.stoploss:
                self.stoploss_eta = self._calculate_eta(self.stoploss)

            if self.target:
                self.target_eta = self._calculate_eta(self.target)

        else:
            self.entry_eta = None
            self.stoploss_eta = None
            self.target_eta = None

    def _calculate_eta(self, price_to_check):
        """Calculate ETA based on price difference"""

        if not price_to_check:
            return TradeETA.FAR

        # Calculate percentage difference
        price_diff_percent = abs((price_to_check - self.last_price) / self.last_price) * 100

        # Define ETA based on percentage difference
        if price_diff_percent <= 0.1:  # 0.1%
            return TradeETA.ONE_MINUTE
        elif price_diff_percent <= 0.2:  # 0.2%
            return TradeETA.FIVE_MINUTES
        elif price_diff_percent <= 0.5:  # 0.5%
            return TradeETA.FIFTEEN_MINUTES
        elif price_diff_percent <= 1.0:  # 1%
            return TradeETA.ONE_HOUR
        elif price_diff_percent <= 2.0:  # 2%
            return TradeETA.ONE_DAY
        elif price_diff_percent <= 5.0:  # 5%
            return TradeETA.ONE_WEEK
        elif price_diff_percent <= 10.0:  # 10%
            return TradeETA.ONE_MONTH
        else:
            return TradeETA.FAR

    @classmethod
    def update_all_etas(cls):
        """Update ETAs for all active trades - can be called periodically"""
        active_trades = cls.query.filter(
            cls.status.in_([TradeStatus.ACTIVE, TradeStatus.ENTRY])
        ).all()

        for trade in active_trades:
            trade.update_etas()

        db.session.commit()

