"""
A horizon based backtest engine
"""

import os 
import abc
import sys 
import logging
from copy import deepcopy

import numpy as np
import pandas as pd

from .datasource import BacktestDataSource
from .broker import Broker
from .context import Context, TradingParam
from .fill import FillStrategy
from .order import Order
from tqdm import tqdm




logger = logging.getLogger(__name__)


class StrategyEnvironment:
    """
    策略运行环境

    Parameters
    --------
    init_cash: float, default 10000000.0
        初始资金
    fill_time: str, default  next_bar
        next_bar, this_bar
    fill_method: str , default vwap
        用于撮合成交的价格
    """
    def __init__(self, init_cash=10000000.0, fill_time='next_bar',
                 fill_method='vwap', commission=None,
                 sllipage=None):
        if fill_time == 'this_bar' and fill_method == 'open':
            logger.warning("以当前开盘价很可能使用到了未来信息")
        self.fill_time = fill_time
        self.fill_strategy = FillStrategy(fill_method=fill_method)

        # 交易撮合成本
        if commission is not None:
            TradingParam.commission = commission
        if sllipage is not None:
            TradingParam.sllipage = sllipage

        # 初始资金
        self.init_cash = init_cash


class FastStrategy(metaclass=abc.ABCMeta):
    """
    策略基类，回测引擎

    创建一个新的策略，只需要派生Strategy类并重载_on_data方法即可

    Parameters
    ----------
    datasource: DataSource
        数据源，应当是复权后的
    env: StrategyEnvironment
        策略环境，策略运行的参数
    name: str
        策略名称
    """

    def __init__(self, datasource, env, name, log_file=None):
        # 数据源
        self._datasource = deepcopy(datasource)

        # 策略运行环境
        self._env = env

        # 策略名称
        self._name = name

        # broker
        self._broker = Broker(env.init_cash, env.fill_strategy)

        # 交易日列表
        # self._dates = pd.to_datetime(dates.get_trade_date(start_date, end_date)).tolist()
        self._dates = sorted(self._datasource.data.index.get_level_values('date').unique())

        # # 证券代码
        # self._sids = self._datasource.data['close'].columns.tolist()
        
        # 组合信息
        self._portfolio_info = None

        # 设置日志
        self.__init_logging(log_file)

    def __init_logging(self, log_file=None):
        """
        设置日志

        Parameters
        ---------
        log_file: str, optional
            给定日志文件路径
        """
        # 初始化日志
        root_logger = logging.getLogger("fast_backtest")
        root_logger.setLevel(logging.DEBUG)

        sh = logging.StreamHandler(self)
        sh.setLevel(logging.WARNING)

        root_logger.addHandler(sh)
        # 添加日志文件
        if log_file:
            fh = logging.FileHandler('{}.log'.format(os.path.join(log_file, self.name)), 'w', 'utf-8')
            fh.setLevel(logging.INFO)

            formatter = logging.Formatter(
                '[%(levelname)s][%(name)s] %(message)s')
            fh.setFormatter(formatter)

            root_logger.addHandler(fh)

    def __on_quote(self, time, quote):
        """
        单一时刻行情响应

        Parameters
        ----------
        time: pd.Timestamp
            当前行情时间
        quotes: dict of pd.Series
            当前时刻的行情
        """
        # 当前时间
        Context.cur_time = time
        # 当前行情
        Context.cur_quote = quote
        if self._env.fill_time == 'next_bar':
            # 响应最新行情，撮合上一时刻发出的订单，更新组合价格
            # 资金不足则停止模拟
            self._broker.on_quote()
            # 策略发出信号
            self._on_data()

        elif self._env.fill_time == 'this_bar':
            # 策略发出信号
            self._on_data()
            # 响应订单，撮合
            self._broker.on_quote()

        #  收盘操作
        # 记录各类组合信息
        self._broker.post_day()
        Context.pre_time = time
        Context.pre_quote = quote

    def _place_order(self, order):
        """
        向broker发送订单, 输入如果是pd.Series则穿件为订单类
        """
        if isinstance(order, pd.Series):
            order = Order(order, Context.cur_time)
        self._broker.place_order(order)

    @abc.abstractmethod
    def _on_data(self):
        """
        策略借口

        在次实现全部逻辑，必要时通过_place_order()方法下达订单

        """

    def run(self):
        """回放行情进行回测"""
        
        quotes = {}
        # 生成当日quotes
        n = len(self._dates)

        with tqdm(total=n, file=sys.stdout, ascii=True, desc="[Fast Backtest] {} In Progress".format(self._name)) as progress:
            for time in self._dates:
                temp = self._datasource.data.loc[time]
                for k in self._datasource.data:
                    quotes.update({k: temp.loc[:, k]})
                self.__on_quote(time, quotes)
                # 下一日开始前重置
                progress.update(1)
                quotes = {}
    # def run(self):
    #     """回放行情进行回测"""
        
    #     quotes = {}
    #     # 生成当日quotes
    #     n = len(self._dates)

    #     for time in self._dates:
    #         temp = self._datasource.data.loc[time]
    #         for k in self._datasource.data:
    #             quotes.update({k: temp.loc[:, k]})
    #         self.__on_quote(time, quotes)
    #             # 下一日开始前重置
    #         quotes = {}

    def rebalance(self, target_portfolio, notional_amount=None, corridor=0., by_weight=True, bench_price='open'):
        """
        调仓投资组合至目标权重

        Parameters
        ----------
        target_portfolio: pd.Series
            权重或者股数
        notional_amount: float
            下期投资组合总权重
        corridor: float
            出发交易的最小成交额，若小于1，则按照notional amount的百分比处理
        by_weight: bool
            是否是权重还是股数

        """
        # 撤销未成交订单
        self._broker.cancel_order()

        # 计算目标组合仓位金额总额, 若notional amount没有提供，择是当前仓位总额(包括现金)
        if notional_amount:
            total_value = notional_amount
        else:
            total_value = self._broker.portfolio.realizable_value + self._broker.portfolio.cash
        # 计算目标投资组合对应每个资产的金额
        if by_weight:
            target_portfolio = target_portfolio.mul(total_value)         
        else:
            target_portfolio = target_portfolio.mul(Context.cur_quote[bench_price], fill_value=0.)
        # 计算调仓金额
        cur_portfolio = Context.cur_quote[bench_price].mul(self._broker.portfolio.pos, fill_value=0.)
        dif_portfolio = target_portfolio.sub(cur_portfolio, fill_value=0.)

        # 当调仓金额小于一定值时，则忽略该调仓, 当小于1时当做百分比
        if 1. > corridor > 0.:
            corridor *= total_value
        dif_portfolio = dif_portfolio[dif_portfolio.abs() > corridor]
        # 计算调仓股数以当前收盘价计算

        # dif_portfolio = np.round(dif_portfolio.div(Context.cur_quote[bench_price], fill_value=0.))\
        #                                       .replace([np.inf, -np.inf], np.nan)
        dif_portfolio = dif_portfolio.div(Context.cur_quote[bench_price], fill_value=0.).replace([np.inf, -np.inf], np.nan).fillna(0.).astype(int)
        # 此处的订单只包括非0的element
        dif_portfolio = dif_portfolio[dif_portfolio.abs() > 0.]
        self._place_order(dif_portfolio)

    # ------------------- 用户获取信息的方法 ---------------------

    def history_placed_order(self, date):
        """
        返回在指定日期下的单(不一定是否成交)

        Parameters
        ---------
        date: str, timestamp
            对应交易日
        
        Returns
        -------
        list of order
        """
        temp = [x for x in self._broker.place_order if x.create_time == pd.Timestamp(date)]
        temp = deepcopy(temp)
        return temp


    def history_pos(self, date=None):
        """
        返回投资组合持仓, 若给定日期，则只返回给定的那一日

        Parameters
        ----------
        date: str, timestamp
            对应交易日

        Returns
        -------
        pd.DataFrame
            index * sids
            sids中只包括曾经有过持仓的
        """
        if date is not None:
            temp = self._broker.pos[pd.Timestamp(date)]
            temp = temp[temp.abs() > 0.]
        else:
            temp = pd.DataFrame(self._broker.pos)
            temp = temp[(temp.fillna(0.) != 0.).any(axis=1)].T
            temp.index.name = 'date'
            temp.columns.name = 'sid'
        return temp

    def history_weight(self, date=None):
        """
        使用收盘价计算当日组合权重, 若给定日期，则只返回给定的那一日

        Parameters
        ---------
        date: str, timestamp
            对应交易日
        
        Returns
        -------
        pd.DataFrame
            index * sid
        """
        if date is not None:
            prc = self._datasource.data.loc[pd.Timestamp('2010-01-08'), 'close']
            pos = self.history_pos(date=date)
            wgt = pos * prc 
            wgt = wgt / (wgt.sum() + self._broker.cash)
        else:
            prc = self._datasource.data['close'].unstack()
            pos = self.history_pos()
            wgt = prc * pos 
            wgt = wgt.div(wgt.sum(axis=1) + self.history_cash, axis=0)
        return wgt


    def history_filled_order(self, date=None):
        """
        返回已经成交的订单, 若给定日期，则只返回给定的那一日

        Parameters
        ----------
        date: str, timestamp
            对应交易日

        Returns
        ------
        pd.DataFrame
            index * sids
            sids中只包括曾经有过订单的
        """
        if date is not None:
            if date in self._broker.filled_order.keys():
                date = pd.Timestamp(date)
                temp = self._broker.filled_order[date]
                temp = temp[temp.abs() > 0.]
            else:
                temp = None
        else:
            temp = pd.DataFrame(self._broker.filled_order)
            temp = temp[(temp.fillna(0.) != 0.).any(axis=1)].T
        return temp

    def history_unfilled_order(self, date=None):
        """
        返回到未能成交的订单, 若给定日期，则只返回给定的那一日

        Parameters
        ----------
        date: str, timestamp
            对应交易日

        Returns
        ------
        pd.DataFrame
            index * sids
            sids中只包括曾有有过未成交订单的
        """
        if date is not None:
            date = pd.Timestamp(date)
            if date in self._broker.unfilled_order.keys():
                temp = self._broker.unfilled_order[date]
                temp = temp[temp.abs() > 0.]
            else:
                temp = None
        else:
            temp = pd.DataFrame(self._broker.unfilled_order)
            temp = temp[(temp.fillna(0.) != 0.).any(axis=1)].T
        return temp

    def history_order(self, date=None):
        """
        返回当日创建的所有订单, 若给定日期, 则返回给定的那一日

        Parameter
        ---------
        date: str, timestamp
            对应交易日

        Returns
        -------
        list
        """
        res = self._broker.place_order
        if date is not None:
            date = pd.Timestamp(date)
            res = [x for x in res if x.create_time==date]
        return res 

    @property
    def history_holding_num(self):
        """
        返回到当前位置所有投资组合的资产个数

        Returns
        ------
        pd.Series
            date
        """
        temp ={x: self._broker.pos[x].fillna(0.).astype(bool).astype(int).abs().sum() for x in self._broker.pos}
        return pd.Series(temp)

    @property
    def history_realizable_value(self):
        """
        返回到当前为止的realizable_value序列

        Returns
        ------
        pd.Series
        """
        return pd.Series(self._broker.realizable_value)

    @property
    def history_cash(self):
        """
        返回到当前为止所有的cash时间序列

        Returns
        ------
        pd.Series
        """
        return pd.Series(self._broker.cash)

    @property
    def history_turnover(self):
        """
        返回当前为止所有的交易额时间序列

        Returns
        ------
        pd.Series
        """
        return pd.Series(self._broker.turnover)

    @property
    def history_transaction_cost(self):
        """
        返回目前为止所有的交易成本 （佣金与印花税）时间序列

        Returns
        ------
        pd.Series
        """
        return pd.Series(self._broker.transaction_cost)

    @property
    def history_market_value(self):
        """
        返回目前为止所有的市值 时间序列

        Returns
        ------
        pd.Series
        """
        return pd.Series(self._broker.market_value)

    @property
    def history_cost_value(self):
        """
        返回当前为止所有的交易成本 时间序列

        Returns
        -------
        pd.Series
        """
        return pd.Series(self._broker.cost_value)

    def history_summary(self):
        """
        返回回测时间序列总结

        包括: cash, security_value, transaction_cost, turnover, holding_num, nav

        Parameters
        ----------
        plot: bool
            是否绘图

        """
        res = pd.DataFrame()
        res['cash'] = self.history_cash
        res['security_value'] = self.history_realizable_value
        res['transaction_cost'] = self.history_transaction_cost
        res['transaction_cost'] = res['transaction_cost'].fillna(0.)
        res['turnover'] = self.history_turnover
        res['turnover'] = res['turnover'].fillna(0.)
        res['holding_num'] = self.history_holding_num
        res['leverage'] = self.history_market_value
        res['nav'] = res['cash'] + res['security_value']

        return res


def buy_and_hold(holding, prcs, strategy_name='default', init_cash=1e8, fill_time='next_bar', fill_method='vwap', commission=None, sllipage=None):
    """
    给定非路径依赖的投资组合，进行回测，返回strategy instance

    Parameters
    ---------
    holding: pd.DataFrame
        投资组合 date * sid 
    prcs: pd.DataFrame
        行情(index sid的MultiIndex)
    strategy_name: str 
        策略名称
    init_cash: int  
        策略初始金额
    fill_time: str 
        next_bar, this_bar
    fill_method: str 
        所用的成交价格: vwap, close
    commission: float
        交易佣金， 默认0.1%
    sllipage: float
        交易滑点, 默认0.2%

    Returns
    ------
    str_inst: strategy instance
    """
    # validate 字段
    assert fill_method in prcs.columns, "传入的行情数据缺少字段{}".format(fill_method)

    start_date = min(holding.index).strftime("%Y%m%d")
    holding = holding.dropna(axis=1, how='all')
    
    # 数据源
    ds = BacktestDataSource(prcs.copy(), start_date, sids_list=holding.columns)
    # 市场环境设置
    env = StrategyEnvironment(init_cash, fill_time, fill_method, commission, sllipage)

    # 定义策略
    class simple_bt_strategy(FastStrategy):
        def __init__(self, datasource, env, name):
            super().__init__(datasource, env, name)
        def _on_data(self):
            if Context.cur_time in holding.index:
                self.rebalance(holding.loc[Context.cur_time])
    
    str_inst = simple_bt_strategy(ds, env, strategy_name)
    str_inst.run()

    return str_inst

