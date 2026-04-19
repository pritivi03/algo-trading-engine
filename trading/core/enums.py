from enum import Enum

class RunMode(str, Enum):
    BACKTEST = 'backtest'
    LIVE = 'live'

class Side(str, Enum):
    BUY = 'buy'
    SELL = 'sell'

class OrderType(str, Enum):
    MARKET = 'market'
    LIMIT = 'limit'

class OrderStatus(str, Enum):
    OPEN = 'open'
    CANCELED = 'canceled'
    FILLED = 'filled'
    REJECTED = 'rejected'

class MarketDataSource(str, Enum):
    HISTORICAL = 'historical'
    LIVE = 'live'
