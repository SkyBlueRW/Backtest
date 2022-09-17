"""
"""

import pandas as pd 

from rqalpha import api, run_func

from . import utils 
from .config import init_stock_config


def rq_backtest(holding, benchmark, matching='next_close', init_cash=1e8, slippage=0.002, plot=True, log_level='error', start_date=None, end_date=None):
    """
    使用rqalpha的回测引擎进行回测

    Parameters
    ----------
    holding: pd.DataFrame
        策略持仓，date * sid 
    benchmark: str 
        业绩基准, 000905.XSHG, 000300.XSHG等
    matching: str 
        next_close, next_open, current_open
        注，在使用next_open进行撮合时，通常会出现大量0订单，原因可能与rqalpha的撮合机制有关
    init_cash: float, int
        默认初始资金
    slippage: float
        回测滑点
    plot: bool
        是否进行绘图
    log_level: str 
        进行log记录的等级：debug, info, warn, error
    
    Returns
    -------
    res: dict 

    """
    holding = holding.copy()
    holding.columns = [utils.convert_to_rq_code(x) for x in holding.columns]
    start_date = min(holding.index) if start_date is None else pd.Timestamp(start_date)
    end_date = max(holding.index) if end_date is None else pd.Timestamp(end_date)
    holding = holding.fillna(0.)

    config = init_stock_config(start_date, end_date, benchmark, matching_type="current_bar", slippage=slippage, 
                               init_cash=init_cash, plot=plot, data_bundle_path="/srv/data/rqbundle/bundle", log_level=log_level)

    def init(context):
        context.stock_sids = holding.columns.tolist()
        context.if_rebalance = False 
    
    def before_trading(context):
        pass 
    
    if matching == 'next_close':
        def after_trading(context):
            td = pd.Timestamp(context.now).date()
            if td in holding.index:
                context.if_rebalance = True 
                context.target_weight = holding.loc[td]

        def handle_bar(context, bar_dict):
            # 调仓日
            if context.if_rebalance:
                # 买单延后
                buy_dict = dict()
                target_p = context.target_weight
                for stk in context.stock_sids:
                    # 当前存在持仓, 下卖单并记录买单
                    if stk in context.portfolio.positions:
                        current_wgt = context.portfolio.positions[stk].quantity * bar_dict[stk].open / context.portfolio.portfolio_value
                        target_weight = target_p.loc[stk]
                        if target_weight < current_wgt:
                            api.order_target_percent(stk, target_weight)
                        elif target_weight > current_wgt:
                            buy_dict.update({stk: target_weight})
                        else:
                            # 无需调仓
                            pass
                    # 当前不存在持仓，存入买单
                    else:
                        target_weight = target_p.loc[stk]
                        buy_dict.update({stk: target_weight})
                # 所有买单
                for i in buy_dict:
                    if buy_dict[i] > 0:
                        api.order_target_percent(i, buy_dict[i])
                context.if_rebalance = False
    
    elif matching == 'current_close':
        def after_trading(context):
            pass 
        def handle_bar(context, bar_dict):
            # 调仓日
            td = pd.Timestamp(context.now).date()
            if td in holding.index:
                context.target_weight = holding.loc[td]
                # 买单延后
                buy_dict = dict()
                target_p = context.target_weight
                for stk in context.stock_sids:
                    # 当前存在持仓, 下卖单并记录买单
                    if stk in context.portfolio.positions:
                        current_wgt = context.portfolio.positions[stk].quantity * bar_dict[stk].open / context.portfolio.portfolio_value
                        target_weight = target_p.loc[stk]
                        if target_weight < current_wgt:
                            api.order_target_percent(stk, target_weight)
                        elif target_weight > current_wgt:
                            buy_dict.update({stk: target_weight})
                        else:
                            # 无需调仓
                            pass
                    # 当前不存在持仓，存入买单
                    else:
                        target_weight = target_p.loc[stk]
                        buy_dict.update({stk: target_weight})
                # 所有买单
                for i in buy_dict:
                    if buy_dict[i] > 0:
                        api.order_target_percent(i, buy_dict[i])


    elif matching == 'next_open':
        config['mod']['sys_simulation']['matching_type'] = 'next_bar'
        
        def after_trading(context):
            pass 
        def handle_bar(context, bar_dict):
            td = pd.Timestamp(context.now).date()
            if td in holding.index:
                target_p = holding.loc[td]
                # 买单延后
                buy_dict = dict()
                for stk in context.stock_sids:
                    # 当前存在持仓, 下卖单并记录买单
                    if stk in context.portfolio.positions:
                        current_wgt = context.portfolio.positions[stk].quantity * bar_dict[stk].close / context.portfolio.portfolio_value
                        target_weight = target_p.loc[stk]
                        if target_weight < current_wgt:
                            api.order_target_percent(stk, target_weight)
                        elif target_weight > current_wgt:
                            buy_dict.update({stk: target_weight})
                        else:
                            # 无需调仓
                            pass
                    # 当前不存在持仓，存入买单
                    else:
                        target_weight = target_p.loc[stk]
                        buy_dict.update({stk: target_weight})
                # 所有买单
                for i in buy_dict:
                    if buy_dict[i] > 0:
                        api.order_target_percent(i, buy_dict[i])
    else:
        raise NotImplementedError("当前只支持next_close, next_open两种成交方式")

    res = run_func(
        init=init,
        handle_bar=handle_bar,
        before_trading=before_trading,
        after_trading=after_trading,
        config=config
    )
    
    # 结果处理
    res = res['sys_analyser']
    res['summary'] = pd.Series(res['summary'])

    res['trades']['order_book_id'] = utils.convert_to_jy_code(res['trades']['order_book_id'])
    res['trades'].index = pd.to_datetime(res['trades'].index)
    res['trades'].index = [x.date() for x in res['trades'].index]
    res['trades'] = res['trades'].rename(columns={'order_book_id': 'sid'})
    res['trades'].index.name = 'date'

    res['portfolio']['benchmark_net_value'] = res['benchmark_portfolio']['unit_net_value']
    del res['benchmark_portfolio']

    res['stock_positions']['order_book_id'] = utils.convert_to_jy_code(res['stock_positions']['order_book_id'])
    res['stock_positions'] = res['stock_positions'].rename(columns={'order_book_id': 'sid'})
    
    res['stock_weight'] = res['stock_positions'].reset_index().pivot(index='date', columns='sid', values='market_value').div(
        res['stock_account']['total_value'], axis=0
    )
    del res['stock_account']
    
    return res 


    