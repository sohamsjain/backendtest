import sqlalchemy as sa


class TradeSide:
    BUY = 'Buy'
    SELL = 'Sell'


trade_side_enum = sa.Enum(TradeSide.BUY, TradeSide.SELL, name='trade_side')


class TradeType:
    BREAKOUT = 'Breakout'
    PULLBACK = 'Pullback'


trade_type_enum = sa.Enum(TradeType.BREAKOUT, TradeType.PULLBACK, name='trade_type')


class TradeStatus:
    ACTIVE = 'Active'
    ENTRY = 'Entry'
    STOPLOSS = 'Stoploss'
    TARGET = 'Target'


trade_status_enum = sa.Enum(TradeStatus.ACTIVE, TradeStatus.ENTRY, TradeStatus.STOPLOSS, TradeStatus.TARGET,
                            name='trade_status')


class TradeTimeframe:
    MINUTE = '1m'
    FIVE_MINUTES = '5m'
    FIFTEEN_MINUTES = '15m'
    HOUR = '1h'
    DAY = '1D'
    WEEK = '1W'
    MONTH = '1M'


trade_timeframe_enum = sa.Enum(TradeTimeframe.MINUTE, TradeTimeframe.FIVE_MINUTES, TradeTimeframe.FIFTEEN_MINUTES,
                               TradeTimeframe.HOUR, TradeTimeframe.DAY, TradeTimeframe.WEEK, TradeTimeframe.MONTH,
                               name='trade_timeframe')


class TradeETA:
    ONE_MINUTE = '1 Minute'
    FIVE_MINUTES = '5 Minutes'
    FIFTEEN_MINUTES = '15 Minutes'
    ONE_HOUR = '1 Hour'
    ONE_DAY = '1 Day'
    ONE_WEEK = '1 Week'
    ONE_MONTH = '1 Month'
    FAR = 'Far'


trade_eta_enum = sa.Enum(TradeETA.ONE_MINUTE, TradeETA.FIVE_MINUTES, TradeETA.FIFTEEN_MINUTES, TradeETA.ONE_HOUR,
                         TradeETA.ONE_DAY, TradeETA.ONE_WEEK, TradeETA.ONE_MONTH, TradeETA.FAR, name='trade_eta')
