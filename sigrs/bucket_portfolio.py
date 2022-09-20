"""
分组测试
"""
import numpy as np 
import pandas as pd 

def cal_sort_quantile(df, name, cut=4, group=None, label=None):
    """
    对变量进行分组(quantile的方式)

    Parameters
    ----------
    df: pd.DataFrame
        MultiIndex的df，包括所有数据
    name: str 
        用于分组的变量名称，应为df中的一列
    cut: int, list
        进行quantile分组的break points
        4: [0, 0.25, 0.5, 0.75, 1.]
        也可以通过 [0, 0.3, 0.7, 1.]进行不平衡分组
    group: str, optional
        分组的conditional因素，如有也应当是df中的一列
    label: list of str, optional
        每一组的名称(由小到大)， 若不给定，则默认为1开始的序列
    
    Returns
    ------
    res: pd.Series
        分组结果
    """
    if isinstance(cut, (list, tuple)):
        n = len(cut) - 1
    else:
        n = cut 
    
    if label is None:
        label = [str(x) for x in range(1, (n+1))]
    else:
        assert len(label) == n, "给定的label个数与分组个数不一致"

    group = ['date'] if group is None else ['date', group]
    
    res = df.groupby(group)[name].apply(
        lambda x: pd.qcut(x, cut, labels=label, duplicates='drop')
    )
    return res 

def cal_sort_bin(df, name, bins=4, group=None, label=None):
    """
    对变量进行分组(bin的方式)

    Parameters
    ----------
    df: pd.DataFrame
        MultiIndex的df，包括所有数据
    name: str 
        用于分组的变量名称，应为df中的一列
    bins: int, list
        进行bins分组的break points
    group: str, optional
        分组的conditional因素，如有也应当是df中的一列
    label: list of str, optional
        每一组的名称(由小到大)， 若不给定，则默认为1开始的序列
    
    Returns
    ------
    res: pd.Series
        分组结果
    """
    if isinstance(bins, (list, tuple)):
        n = len(bins) - 1
    else:
        n = bins 
    
    if label is None:
        label = [str(x) for x in range(1, (n+1))]
    else:
        assert len(label) == n, "Number of label is different from number of bins"
    
    group = ['date'] if group is None else ['date', group]

    res = df.groupby(group)[name].apply(
        lambda x: pd.cut(x, bins, labels=label, duplicates='drop')
    )
    return res 

def cal_bucket_ret(sort, ret, weight=None, delay=1):
    """
    Calculate bucket return 

    Parameters
    ----------
    sort: pd.DataFrame
        date * sid 信号分组结果
    ret: pd.DataFrame
        date * sid 日频收益率
    weight: pd.DataFrame
        date * sid 收益率的加权权重，若为None则等权
    delay: int
        延后天数
    
    Returns
    ------
    res: pd.DataFrame
        各个分组与全样本的表现
    """
    # 对齐分组与收益率
    # 以分组的列为universe， 将分组对齐到日频(且有收益率)
    sort, ret = sort.align(ret.loc[:, sort.columns], join='right', copy=True)
    sort = sort.ffill().shift(delay).dropna(how='all')

    # 若不提供权重，则等权
    if weight is None:
        weight = pd.DataFrame(1., index=sort.index, columns=sort.columns)
    else:
        weight = weight.loc[:, sort.columns].reindex(ret.index).ffill().shift(delay).loc[sort.index]
    ret = ret.loc[sort.index]

    groups = np.unique(sort).tolist()
    if 'nan' in groups:
        groups.remove('nan')

    mask = np.logical_and(sort.notna(), ret.notna()) 
    
    res = pd.DataFrame(index=sort.index, columns=groups)
    for gp in groups:
        res[gp] = (ret.where(sort == gp).where(mask) * weight.where(sort == gp)).sum(axis=1) / weight.where(sort == gp).where(mask).sum(axis=1)

    res['all'] = (ret.where(mask) * weight).sum(axis=1) / weight.where(mask).sum(axis=1)
    
    
    return res 

