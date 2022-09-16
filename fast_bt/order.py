"""
Order Object
"""

import pandas as pd

class Order:
    """
    Order Object that contains all trading information on a given snapshot 

    Attributes
    ----------
    time: pd.Timestamp
        Time that the order created
    quantity: pd.Series
        Trading booked to execute
    price: pd.Series
        Settlement price
    filled_quantity: pd.Series
        Successful fill of booked trading
    filled_price: pd.Series
        Price of successful fill (taken slippage and transaction fee in consideration)
    status: str
        Status of the order: unfilled, filled
    """
    def __init__(self, quantity, create_time, price=pd.Series()):
        assert isinstance(quantity, pd.Series) and isinstance(price, pd.Series), "Both price and order should be passed in terms of pd.Series" 
        self.price = price
        self.create_time = create_time
        self.quantity = quantity
        self.filled_quantity = pd.Series()
        self.filled_price = pd.Series()
        self.status = 'unfilled'
        self.transaction_amount = 0.                    # + means buy with cash, - means sell security
        self.abs_transaction_amount = 0.
        self.transaction_cost = 0.
