"""
IC analysis 
"""

import numpy as np 
import pandas as pd 

def cal_ic(signal, ret, universe=None, method='pearson'):
    """
    计算股票截面ic

    Parameters
    ---------
    signal: pd.DataFrame
        date * sid的信号
    ret: pd.DataFrame   
        date * sid的收益率
    universe: pd.DataFrame
        date * sid的股票池
    method: str 
        计算ic的方法 [pearson, spearman]
    
    Returns
    -------
    pd.Series:
        时间序列ic
    """
    idx = signal.index.intersection(ret.index)
    cols = signal.columns.intersection(ret.columns)
    signal = signal.copy()
    ret = ret.copy()

    if universe is not None:
        idx = idx.intersection(universe.index)
        cols = cols.intersection(universe.columns)
        signal = signal.loc[idx, cols].where(universe.loc[idx, cols])
        ret = ret.loc[idx, cols].where(universe.loc[idx, cols])
    else:
        signal = signal.loc[idx, cols]
        ret = ret.loc[idx, cols]

    return signal.corrwith(ret, axis=1, method=method) 


# ----------------------- ic 相关指标 -----------------

def cal_ic_summary(ic, L_threshold=0.):
    """
    计算ic序列的表现总结

    Parameters
    ----------
    ic: pd.Series
        ic时间序列
    L_threshold: float
        用于计算Sharpe-Omega的阈值
    
    Returns
    -------
    pd.Series
        表现指标总结
    """
    ic = ic.dropna()
    idx = []
    val = []

    # ir 
    idx.append("IR")
    val.append('{0:.3f}'.format(ic.mean() / ic.std()))

    # sharpe omega
    idx.append("Sharpe-Omega")
    omega_val = L_threshold - ic 
    omega_val = np.sum(omega_val[omega_val >=0]) / len(ic)
    omega_val = (ic.mean() - L_threshold) / omega_val 
    val.append('{0:.2f}'.format(omega_val))

    # 均值
    idx.append("Mean")
    val.append('{0:.3f}'.format(ic.mean()))

    # 标准差
    idx.append("Std")
    val.append('{0:.3f}'.format(ic.std()))

    # 偏度
    idx.append("Skew")
    val.append('{0:.3f}'.format(ic.skew()))

    # 峰度
    idx.append("Kurt")
    val.append('{0:.3f}'.format(ic.kurt()))

    # 胜率
    idx.append("Win Rate")
    win_rate = ic[ic>0]
    win_rate = len(win_rate) / len(ic)
    val.append('{0:.1%}'.format(win_rate))

    return pd.Series(val, index=idx)


def cal_yearly_ic_summary(ic, L_threshold=0.):
    """
    计算年度ic指标
    """
    return ic.groupby(lambda x: x.year).apply(lambda x: cal_ic_summary(x, L_threshold)).unstack().T  
