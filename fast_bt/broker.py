"""
A broker
"""

import logging
from copy import deepcopy

import pandas as pd

from .portfolio import Portfolio
from .context import Context

logger = logging.getLogger(__name__)


class Broker:
    """
    模拟 Broker 接收撮合订单


    """
    def __init__(self, init_cash, fill_strategy):
        # 投资组合
        self.portfolio = Portfolio(init_cash)
        # 成交模型
        self.__fill_strategy = fill_strategy
        # 成功执行的订单 / 时间切片数据，只在当日有效
        self.__filled_order = []
        # 未能成功执行的订单部分 / 时间切片数据，只在当日有效
        self.__cancelled_order = []
        # 等待执行的订单 / 时间切片数据，只在当日有效
        self.__active_orders = []
        # 持仓
        self.pos = dict()
        # 成交订单
        self.filled_order = dict()
        # 未成交订单
        self.unfilled_order = dict()
        # 现金
        self.cash = dict()
        # realizable价值
        self.realizable_value = dict()
        # 成本价格
        self.cost_value = dict()
        # 总市值
        self.market_value = dict()
        # 交易成本 (包括commission与tax)
        self.transaction_cost = dict()
        # 交易额
        self.turnover = dict()
        # 下的订单
        self.placed_order = []

    def place_order(self, order):
        """
        下单

        将订单加入待执行list
        """
        self.__active_orders.append(order)

    def cancel_order(self):
        """
        停止当前所有待执行定单

        """
        self.__active_orders = []

    def _list_active_orders(self):
        """
        用于validate
        """
        return deepcopy(self.__active_orders)

    def on_quote(self):
        """
        响应行情

        1. 撮合上一阶段订单
        2. 更新portfolio价格
        """
        # 判断是否有订单
        if self.__active_orders:
            quote = Context.cur_quote
            for order in self.__active_orders:
                # 撮合订单, 并返回未成交的订单
                unfilled = self.__fill_strategy.fill_order(order, quote)
                # 根据撮合结果更新投资组合信息
                self.portfolio.update_by_order(order)
                # 订单中未能成功执行的部分
                self.__cancelled_order.append(unfilled)
                # 订单中执行成功的部分
                self.__filled_order.append(order)
                self.__active_orders = [
                    order for order in self.__active_orders if order.status == 'unfilled'
                ]
                self.placed_order.append(order)
        self.portfolio.update_by_price()

    def post_day(self):
        """
        在当日结束后记录组合信息

        """
        # 仓位记录
        self.pos.update({Context.cur_time: self.portfolio.pos})
        # 记录成交订单记录
        if self.__filled_order:
            filled_order = pd.Series()
            trn_cost = 0.
            trn_amount = 0.
            for order in self.__filled_order:
                filled_order = filled_order.add(order.filled_quantity, fill_value=0.)
                trn_cost = trn_cost + order.transaction_cost
                trn_amount = trn_amount + order.abs_transaction_amount
            self.filled_order.update({Context.cur_time: filled_order})
            self.transaction_cost.update({Context.cur_time: trn_cost})
            self.turnover.update({Context.cur_time: trn_amount})
        # 记录未成交订单记录
        if self.__cancelled_order:
            unfilled_order = pd.Series()
            for order in self.__cancelled_order:
                unfilled_order = unfilled_order.add(order, fill_value=0.)
            self.unfilled_order.update({Context.cur_time: unfilled_order})

        # 现金记录
        self.cash.update({Context.cur_time: self.portfolio.cash})
        # 可实现价值记录
        self.realizable_value.update({Context.cur_time: self.portfolio.realizable_value})
        # 成本价值记录
        self.cost_value.update({Context.cur_time: self.portfolio.cost_value})
        # 总市值
        self.market_value.update({Context.cur_time: self.portfolio.market_value})

        # 清空当日信息

        self.__filled_order = list()
        self.__cancelled_order = list()

    def return_filled_order(self):
        return deepcopy(self.__filled_order)

    def return_unfilled_order(self):
        return self.deepcopy(__cancelled_order)

    def return_active_order(self):
        return self.deepcopy(__active_orders)






