"""
Constant variable
"""


class Context:
    """
    The Global variable to keep track of current market quote

    Atttribute
    ----------
    cur_time: pd.Timestamp
        current time
    pre_time: pd.Timestamp
        time one step ago
    cur_prc: dict
        current market quote, each key should be a field (price, volume, etc) in pd.Series
    pre_prc: dict
        previous market quote
    """
    cur_time = None
    pre_time = None
    cur_quote = {}
    pre_quote = {}


class TradingParam:
    """
    Constant used across backtest
    """
    # sllipage
    sllipage = 0.002
    # commission
    commission = 0.001
    # max percentage of the snapshot's amount that are allowed 
    max_trading_percentage = 0.05