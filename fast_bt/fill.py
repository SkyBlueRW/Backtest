"""
Method to fill
"""

import numpy as np
import pandas as pd

from .context import TradingParam


class FillStrategy:
    """Method to fill, should consider transaction cost here"""
    def __init__(self, fill_method):
        self.fill_method = fill_method

    def fill_order(self, order, quote):
        """
        execute the trade

        1. adjust the market price with sllipage to get settlement price
        2. adjust filled order according to market info
        3. calculate transaction volume and transaction cost
        4. return orders that are not filled sucessefully

        Parameters
        ---------
        order: order
            Order instance
        quote: dict
            market quote of the snapshot
        sllipage: float
            slippage, as percentage
        commission: float
            commission, as percentage

        Return
        ------
        cancelled_order: pd.Series
            orders failed

        """
        # take input to determine what price to use (close, vwap, twap, etc...)
        if self.fill_method in quote:
            order.price = quote[self.fill_method]
        else:
            raise Exception("Illegit price type")
        if order.status == 'unfilled':    
            # Only security with positive price will be deemed as tradable, nan and 0 will be ignored
            order.filled_quantity = order.quantity.mul((order.price > 0.).astype(float), fill_value=0.)
            # Adjust price to reflect sllipage as a percentage
            order.filled_price = order.price.add(order.price.mul(np.sign(order.quantity).mul(TradingParam.sllipage), fill_value=0.), fill_value=0.) 
            # Check if there is a restriction in maximum trading percentage.
            # If yes, reduce the filled amount to threshold
            if 'amount' in quote:
                # maximum amount as a percentage of market amount of the snapshot
                max_tran_share = quote['amount'] * TradingParam.max_trading_percentage // order.filled_price ## maximum share to trade 
                max_tran_share
                # reduce those exceeding the max share 
                order.filled_quantity = order.filled_quantity.where(np.abs(order.filled_quantity) < max_tran_share)\
                                             .fillna(np.sign(order.filled_quantity) * max_tran_share)
            # Log trading information
            transaction_amt = order.filled_price.mul(order.filled_quantity, fill_value=0.)
            order.abs_transaction_amount = np.abs(transaction_amt).sum()
            order.transaction_amount = transaction_amt.sum()
            # Calculate commision and tax of 0.1% (for sell only)
            order.transaction_cost = order.abs_transaction_amount * TradingParam.commission - transaction_amt[transaction_amt < 0.].sum() * 0.001

            # Log faied order 
            cancelled_order = order.quantity.sub(order.filled_quantity, fill_value=0.)
            cancelled_order = cancelled_order[cancelled_order.abs() > 0.]
            order.filled_quantity = order.filled_quantity[order.filled_quantity.abs() > 0.]

            order.status = 'filled'
            return cancelled_order
        else:
            raise Exception("Casn not pass in legit order to execute: {}".format(order.create_time.strftime("%Y-%m-%d")))





