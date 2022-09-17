"""
long short portfolio backtest
"""
import sys 
import os 
path = os.path.dirname(os.path.dirname(__file__))
if path not in sys.path:
    sys.path.append(path)

from fast_bt import simple_bt

def long_short_backtest(signal, prcs, universe=None, init_cash=1e8, fill_time='this_bar', fill_method='vwap', commission=None, sllipage=None):
    """
    对信号进行多空组合测试

    Parameters
    ---------
    signal: pd.DataFrame
        date * sid 信号
    prcs: pd.DataFrame
        MultiIndex 价格
    universe: pd.DataFrame, optional    
        股票池(force 到指定股票池，无数据为0)
    
    Return
    -------
    res: pd.DataFrame   
        测试结果: cash, security_value, transaction_cost, turnover, holding_num, leverage, nav
    """
    signal = signal.copy()
    if universe is not None:
        idx = signal.index.intersection(universe.index)
        cols = signal.columns.intersection(universe.columns)
        signal = signal.loc[idx, cols].where(universe.loc[idx, cols])

    # 去极值
    up_thres = signal.quantile(0.99, axis=1, numeric_only=True)
    down_thres = signal.quantile(0.01, axis=1, numeric_only=True)
    mask = signal.notna()
    signal = signal.T 
    signal = signal.where(signal.le(up_thres, axis=1)).fillna(up_thres)
    signal = signal.where(signal.ge(down_thres, axis=1)).fillna(down_thres)
    signal = signal.T.where(mask)
    if universe is not None:
        signal = signal.fillna(0.).loc[idx, col].where(universe.loc[idx, cols])

    signal = signal.sub(signal.mean(axis=1), axis=0)
    signal = signal.div(signal.abs().sum(axis=1), axis=0) * 0.9 

    return simple_bt(signal, prcs, "longshort_sig", init_cash, fill_time, fill_method, commission, sllipage).history_summary()

