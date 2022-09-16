"""
某一时间截面上投资组合

"""
import copy
import logging

import numpy as np
import pandas as pd

from .context import Context

logger = logging.getLogger(__name__)


class Portfolio:
    """
    Portfolio 类
    
    一个时间截面上的资产组合为一个Portfolio, 此外还包括现金
    
    1. 方法update_by_price:
        行情数据触发，根据新的行情信息，更新投资组合的信息(不改变持仓)
    2. 方法update_by_order:
        订单触发，根据新的订单，更新投资组合持仓信息 (当现金小于0时报错)
    
    Parameters
    ----------

    init_cash: float
        初始资金
        
    Attributes
    ---------
    cash: float
        扣除手续费和交易税后投资组合中剩余的自由现金
    pos: pd.Series
        对应每只股票对应的股数
    market_value: float
        仓位绝对值加总
    """
    def __init__(self, init_cash):
        self.cash = init_cash               # 初始资金
        self.pos = pd.Series()              # 初始组合
        self.realizable_value = 0.          # 证券变现值
        self.market_value = 0.              # 证券总市值
        self.cost_value = 0.                # 投资组合总成本价格

    def update_by_price(self, benchmark='close'):
        """
        根据行情更新仓位，现金没有变化
            1. 调整market_value
            2. 调整realizable_value
        """
        pos_value = self.pos.mul(Context.cur_quote[benchmark], fill_value=0.)
        self.market_value = np.abs(pos_value).sum()
        self.realizable_value = pos_value.sum()

    def update_by_order(self, order):
        """
        根据已成交的订单
            1. 调整股票仓位
            2. 调整成本价格 (cost_value)
            3. 调整现金仓位 (cash)
        """
        if order.status == 'filled':
            self.pos = self.pos.add(order.filled_quantity, fill_value=0.)
            self.cost_value = self.cost_value + order.transaction_amount
            self.cash = self.cash - order.transaction_amount - order.transaction_cost
        else:
            logger.error("【{}】订单未正确处理".format(Context.cur_time))
        if self.cash < 0:
            logger.info("【{}】现金余额不足：【{}】\n ".format(Context.cur_time, self.cash))
            # raise Exception("现金不足")





