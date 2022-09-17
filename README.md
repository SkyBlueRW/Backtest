# Backtest

A backtest engine for cross section strategies.

    - assume constant event time interval (days, hours, weeks, etc)
    - vectorized calculation for all securiteis at a give horizon to speed up
    - event driven in the sense of different horizons to enable flexibility

Backtest results just show some sense of the strategy. Historical performance is almost never a good estimation of future performance (especially historical performance from backtest).

**Motivation**

Event driven backtest engines (Zipline as an example) usually loop through events (market quote update, order action ..etc) in significant grangularities. Such design enable the engine to handle all kinds of strategy scenarios as well as provide enhancement possibilities (trading model, etc..). While there is a cost for such high level of gragularities. The number of events (in proportion with time required to run) increased significantly when there are large number of securities in the universe. (N * T * K)

While in the research of cross sectional strategies, such kind of high level grangularity is usually unnecessary. For one hand, there are  very large number of securiteis (a couple of thousands or even tens of thousands). Such kind of strategies usually rely on universe breadth to turn weak cross sectional prediction to risk aware portfolios and make the backtest quite time consuming. On the other hand, this demand for breadth also restrict cross sectional strategies to a stable framework that each horizon instead of each security at all horizons can be used as basic unit to reduce run time error. 

Hence I developed this backtest engine designed specifically for cross section strategies. It take all securitis at a horizon as the basci unit and use vectorized calculation to speed up the process. 

**Pesudo Implementation**
strategy.run:
    for t in ALL_horizons:
        - Update market quote for t 
        - Place order
        - Update info with market quote (or before place order depending on setting)
        

# Demo 

**Low level usage**

```python
from fast_bt import FastStrategy

# load data
ds = BacktestDataSource(price, start_date)
# Load Environment variable
env = StrategyEnvironment(init_cash, fill_time, fill_method, commission, sllipage)

# Define your strategy
class simple_bt_strategy(FastStrategy):
    def __init__(self, datasource, env, name):
        super().__init__(datasource, env, name)
    def _on_data(self):
        # A simple strategy of buy and hold
        if Context.cur_time in dates:
            self.rebalance(holding.loc[Context.cur_time])

        # can also get holding / market quote info via to specify path dependent behavior
        # str_inst.history_order(date)
        # str_inst.history_holding_num
        # str_inst.history_realizable_value
        # str_inst.history_cash
        # str_inst.history_turnover
        # str_inst.history_transaction_cost
        # str_inst.history_market_value
        # str_inst.history_cost_value

str_inst = simple_bt_strategy(ds, env, strategy_name)
str_inst.run()

# give yhou time series of cash, security value, transaction cost, turnover, holding num for each security, leverage and net value as pd.DataFrame
str_inst.history_summary



```

**API for buy and hold**

```python
from fast_bt import buy_and_hold
str_inst = buy_and_hold(holding, prcs, strategy_name='default', init_cash=1e8, fill_time='next_bar', fill_method='vwap', commission=None, sllipage=None)
```





<!-- ## rq_bt 
基于rqalpha的回测工具包
通常通过rq_backtest(holding, benchmark, matching='next_close', init_cash=1e8, slippage=0.002, plot=True, log_level='error') 来进行快速的调用

## fast_bt 
基于截面的快速回测，用于快速的尝试
通常通过simple_bt(holding, prcs, strategy_name='default', init_cash=1e8, fill_time='next_bar', fill_method='vwap', commission=None, sllipage=None) 来进行快速的调用 -->

