"""
Fast Backtest

fast backtest framework: backtest in unit of horizon. The basis unit is pd.Series

1. 回测运行逻辑
strategy.run:
    for time in 所有交易日:
        //更新行情至quotes
        --------------------  Context.cur_time = t
        //strategy.__on_quote(time, quotes)   # 核心功能模块，包括行情，组合更新，下单等功能
            //更新时间与行情至Context (Context.cur_time, Context.cur_quote), 注 Context是公用变量，可以在回测的各个位置进行调用
            //根据当前bar下单或者下一个bar下单来确定顺序进行 broker.on_quote, 以及strategy._on_data
            //broker.on_quote     # 按顺序进行如下2中功能操作
                //撮合 broker.__active_order中的订单 (可能是多个订单)
                    //Fill撮合订单，Portfolio.update_by_order, 记录成交与未成交订单, 记录下的订单
                //Portfolio.update_by_price,  # 使用收盘价更新投资组合信息
            //strategy._on_data   # 此处为策略逻辑，进行下单
            //broker.post_day 处理  # 记录并更新broker的各类信息, 重置__filled, __unfiledd
            //更新Context.pre_time, Context.pre_quote
        ------------------   当日处理完毕，接下来的所有操作都是以Context.cur_time = t + 1 进行 (因此 次数如果_on_data在on_quote之后会在下一个bar成交)


"""

from .datasource import BacktestDataSource
from .context import Context 
from .strategy import FastStrategy, StrategyEnvironment, buy_and_hold