"""
Object to deal with data
"""

import os
import copy

import numpy as np
import pandas as pd



class BacktestDataSource:
    """
    data source 
    """

    def __init__(self, data, start_date=None, end_date=None, sids_list=None):
        """
        Data source

        It should be adjusted price in form of pd.MultiIndex DataFrame
        It should be noted that data should also contain close price of suspended securities to update net value

                            open	    close	    vwap	    amount
        date	    sid				
        2010-01-04	000001	830.053576	802.633372	811.939526	5.802495e+08
        """
        self.data = copy.deepcopy(data)
        if start_date is not None:
            self.data = self.data.loc[pd.Timestamp(start_date): ]
        if end_date is not None:
            self.data = self.data.loc[:pd.Timestamp(end_date)]
        if sids_list is not None:
            self.data = self.data.query("sid in {}".format(
                str(tuple(sids_list)).replace(',)', ')')
            ))

        self._check_valid(self.data)


    @staticmethod
    def _check_valid(data):
        """check if data is legit"""
        assert "close" in data, "close is a requred field"
        assert isinstance(data.index.get_level_values(level='date'),
                          pd.DatetimeIndex)

        # # 检查index
        # for k in data:
        #     assert (data['close'].index == data[k].index).all(), "{}的index错误".format(k)
        # # 检查columns
        # for k in data:
        #     assert (data['close'].columns == data[k].columns).all(), "{}的column错误".format(k)

