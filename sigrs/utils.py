"""
return compunding
"""

import numpy as np 
import pandas as pd 


def compounding_forward_prc(prcs, interval, delay=0, amount_df=None, amount_threshold=5e6):
    """
    根据复权价格，计算每一交易日的forward looking收益率

    Parameters
    ---------
    prcs: pd.DataFrame
        复权的价格
    interval: int 
        收益率的period
    delay: int
        延后交易的天数
    amount_df: pd.DataFrame
        成交额
    amount_threshold: float
        用于判断当天是否可以成功交易的阈值
    
    Returns
    -------
    res: pd.DataFrame
        收益率
    """
    res = prcs.shift(-delay)\
              .pct_change(periods=interval)
    if amount_df is not None:
        res = res.where(amount_df.shift(-delay) >= amount_threshold)
        res = res.where(amount_df.shift(interval-delay) >= amount_threshold)
    
    res = res.shift(-interval)
    return res.dropna(how='all')


def compounding_forward_ret(ret, interval, delay=0, amount_df=None, amount_threshold=5e6):
    """
    根据每日收益率(当日收益率为当日价格相比前一日价格)，计算每一交易日的forward looking收益率

    Parameters
    ---------
    prcs: pd.DataFrame
        复权的价格
    interval: int 
        收益率的period
    delay: int
        延后交易的天数
    amount_df: pd.DataFrame
        成交额
    amount_threshold: float
        用于判断当天是否可以成功交易的阈值
    
    Returns
    -------
    res: pd.DataFrame
        收益率
    """
    res = (ret + 1).cumprod()
    res = res.shift(-delay)\
              .pct_change(periods=interval)
    if amount_df is not None:
        res = res.where(amount_df.shift(-delay) >= amount_threshold)
        res = res.where(amount_df.shift(interval-delay) >= amount_threshold)
    
    res = res.shift(-interval)
    return res

