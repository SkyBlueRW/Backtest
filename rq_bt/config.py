"""
config 示例
"""

import pandas as pd 

from . import utils

def init_stock_config(start_date, end_date, benchmark, matching_type="next_bar", slippage=0.002, init_cash=1e8, plot=True, data_bundle_path="/srv/data/rqbundle/bundle", log_level='error'):
    """
    生成股票回测config

    Parameters
    ----------
    start_date, end_date: timestamp
        回测起止时间
    benchmark: str  
        业绩基准代码
    matching_type: str
        撮合方式
        current_bar: 当前bar收盘价
        next_bar: 下一个bar开盘价
    slippage: float
        滑点
    init_cash: float
        起始资金
    plot: bool
        是否进行绘图
    data_bundle_path: str 
        数据源地址
    log_level: str 
        策略回测的log级别 verbose, info, warning, error
    
    Returns
    ------
    config: dict 
    """
    config = {
        "base": {
            "data_bundle_path": data_bundle_path,
            "start_date": pd.Timestamp(start_date).strftime("%Y-%m-%d"),
            "end_date": pd.Timestamp(end_date).strftime("%Y-%m-%d"),
            "run_type": "b",
            "frequency": "1d",
            "accounts":{
                "stock": init_cash
            }
        },
        "extra":{
            "log_level": log_level
        },
        "mod":{
            "sys_simulation":{
                "enabled": True,
                "matching_type": matching_type,
                "slippage_model": "PriceRatioSlippage",
                "slippage": slippage
            },
            "sys_analyser": {
                "enabled": True,
                'plot': plot,
                'benchmark': benchmark
            },
            "sys_transaction_cost":{
                "enabled": True,
                # A股最小手续费
                "cn_stock_min_commission": 5,
                # 港股最小手续费
                "hk_stock_min_commission": 50,
                # 设置手续费乘数，默认为1
                "commission_multiplier": 1,
            }
        }
    }
    return config


config = {
    "base": {
        # 数据文件地址
        "data_bundle_path": "/srv/data/rqbundle",
        # 策略文件路径
        "strategy_file": "strategy.py",
        "start_date": "2015-01-09",
        "end_date": "2015-03-09",
        # 保证金乘数，默认为1 
        "margin_multiplier": 1,
        # 运行类型，b为回测，p为模拟交易，r为实盘交易
        "run_type": 'b',
        # 1d为日线回测，1m为分钟线回测
        "frequency": "1d",
        # 对应账户的初始资金
        "accounts": {
            "stock": 100000,
            'future': 0
        },
        # 初始仓位
        "init_positions": {}
    },

    "extra":{
        # 输出级别分别为verbose, info, warning, error.其中verbose为查看最详细的日志
        "log_level": 'info',
        "user_system_log_disabled": False,
        "user_log_disabled": False, 
        # 启动性能分析
        "enable_profiler": False,
        "is_hold": False,
        "locale": "zh_Hans_CN",
        'logger': []
    },

    "mod": {
        "sys_simulation": {
            "enabled": True,
            # 是否开启信号模式
            "signal": False,
            # 启用的回测引擎，目前支持 `current_bar` (当前Bar收盘价撮合) 和 `next_bar` (下一个Bar开盘价撮合)
            "matching_type": "current_bar",
            # price_limit: 在处于涨跌停时，无法买进/卖出，默认开启【在 Signal 模式下，不再禁止买进/卖出，如果开启，则给出警告提示。】
            "price_limit": True,
            # liquidity_limit: 当对手盘没有流动性的时候，无法买进/卖出，默认关闭
            "liquidity_limit": False,
            # 是否有成交量限制
            "volume_limit": True,
            # 按照当前成交量的百分比进行撮合
            "volume_percent": 0.25,
            # 滑点模型，如果使用自己的定制的滑点，需要加上完整的包名
            "slippage_model": "PriceRatioSlippage",
            # 设置滑点
            "slippage": 0.001,
        },
        "sys_accounts": {
            "enabled": True,
            # 开启/关闭 股票 T+1， 默认开启
            "stock_t1": True,
            # 分红再投资
            "dividend_reinvestment": False,
            # 强平
            "future_forced_liquidation": True,
            # 当持仓股票退市时，按照退市价格返还现金
            "cash_return_by_stock_delisted": True,
            # 股票下单因资金不足被拒时改为使用全部剩余资金下单
            "auto_switch_order_value": False
        },
        "sys_analyzer": {
            "enabled": True,
            # 当不输出csv/pickle/plot 等内容时，可以通过 record 来决定是否执行该 Mod 的计算逻辑
            "record": True,
            # 如果指定路径，则输出计算后的 pickle 文件
            "output_file": None,
            # 如果指定路径，则输出 report csv 文件
            "report_save_path": None,
            # 画图
            'plot': False,
            # 如果指定路径，则输出 plot 对应的图片文件
            'plot_save_file': None
        },
        "sys_progress": {
            "enabled": True,
            # 启用进度条
            "show": True
        },
        "sys_risk": {
            "enabled": True,
            # 检查限价单价格是否合法
            "validate_price": True,
            # 检查标的证券是否可以交易
            "validate_is_trading": True,
            # 检查可用资金是否充足
            "validate_cash": True,
            # 检查股票可平仓位是否充足
            "validate_stock_position": True,
            # 检查期货可平仓位是否充足
            "validate_future_position": True,
            # 检查是否存在自成交的风险
            "validate_self_trade": False,
        },
        "sys_transaction_cost":{
            "enabled": True,
            # A股最小手续费
            "cn_stock_min_commission": 5,
            # 港股最小手续费
            "hk_stock_min_commission": 50,
            # 设置手续费乘数，默认为1
            "commission_multiplier": 1,
        }
    }
}