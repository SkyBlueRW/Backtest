# Backtest

A backtest engine for cross section strategies.


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
    
str_inst = simple_bt_strategy(ds, env, strategy_name)
str_inst.run()
```

**API for buy and hold**

```python
from fast_bt import buy_and_hold
buy_and_hold(holding, prcs, strategy_name='default', init_cash=1e8, fill_time='next_bar', fill_method='vwap', commission=None, sllipage=None)
```





<!-- ## rq_bt 
基于rqalpha的回测工具包
通常通过rq_backtest(holding, benchmark, matching='next_close', init_cash=1e8, slippage=0.002, plot=True, log_level='error') 来进行快速的调用

## fast_bt 
基于截面的快速回测，用于快速的尝试
通常通过simple_bt(holding, prcs, strategy_name='default', init_cash=1e8, fill_time='next_bar', fill_method='vwap', commission=None, sllipage=None) 来进行快速的调用 -->

