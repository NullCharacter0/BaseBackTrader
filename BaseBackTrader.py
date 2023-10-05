from typing import Any
from pandas import DataFrame



class BaseBackTrader:
    # _______Modifiers_______ 
    long_quantity_multi:float = 1 
    short_quantity_multi:float = 1
    base_percentage = 4 
    pct_inc_value = 1 
    last_signal : str = ""
    increment_percentage = True # If last_trade == Current_trade: [long/short]_percentage + pct_inc_value 
    # _______________________
    # ______ Logistics ______
    successful_Long_trades = 0 # +1 if Buy
    successful_Short_trades = 0# +1 if Sell
    unsuccessful_trades = 0# +1 if A check returns False 
    profitable_trades = 0  # +1 if Log hits a Target 
    unprofitable_trades = 0  # +1 if Log hit a StopLoss
    amount_risked_dollars = 0 # +1 for every dollar risked
    amount_risked_stock = 0 # +1 for every stock risked
    amount_difference_dollars = 0 #  Beginning value - Ending value  
    amount_difference_stock = 0 # Beginning value - Ending value  
    total_amount_difference = 0 # IN Dollars Beginning value - Ending value  
    # ________________________
    # _________Values_________
    starting_stock_quantity: float 
    starting_dollar_quantity: float
    starting_total_value:float
    ending_stock_quantity: float 
    ending_dollar_quantity: float 
    ending_total_value:float
    ticker: str
    data_frame: DataFrame
    analytics: DataFrame

    # ________________________
    
    # _________Limits_________
    minimum = 0.5 # min Order size in dollar. ( MUST convert stock to its dollar equivalent)
    # _________________________
    
    
    def __init__(self, data_frame:DataFrame,analytics:DataFrame,  stock_quantity:float= 0.5, dollar_quantity:float=100,):
        self.data_frame = data_frame
        self.starting_price = 0 if data_frame.empty else data_frame.close.iloc[0]
        self.starting_stock_quantity =  self.full_stock_quantity = stock_quantity # Starting / FULL Stock/Crypto amount
        self.starting_dollar_quantity = self.full_dollar_quantity = dollar_quantity # Starting / FULL Dollar amount
        self.starting_total_value = self.convert_stock2dollar(self.full_stock_quantity,self.starting_price) + self.full_dollar_quantity
        self.long_percentage = self.base_percentage 
        self.short_percentage = self.base_percentage 
        self.analytics=analytics
        pass
    @staticmethod    
    def convert_stock2dollar(quantity:float,closing_price:float ) -> float:
        """Converts given stock and converts it to its dollar equivalent 


        Args:
            quantity (float): Stock quantity
            closing_price (float): closing price

        Returns:
            float: stock_value ( EG: $10.5 )
        """
        return quantity * closing_price
    @staticmethod    
    def convert_dollar2stock(dollar_amt,closing_price) -> float:
        """Converts given dollar and converts it to its stock equivalent 


        Args:
            dollar (float): dollar quantity
            closing_price (float): closing price

        Returns:
            float: stock_quantity ( EG: 0.003 )
        """
        return dollar_amt / closing_price
    
    def pct_calc_dollar_quantity(self) -> float: 
        return self.full_dollar_quantity * (self.long_percentage/100)
        
    def pct_calc_stock_quantity(self) -> float: 
        return self.full_stock_quantity * (self.short_percentage/100)
        
    def can_buy_pct(self)-> bool:
        return self.pct_calc_dollar_quantity() > self.minimum
    
    def can_sell_pct(self,closing_price=1500)-> bool:
        return self.convert_stock2dollar(self.pct_calc_stock_quantity(), closing_price) > self.minimum
            
    def buy_pct(self,price):
        # Calculate how much your willing to use
        if self.increment_percentage == True:
            if self.last_signal == "Long": self.long_percentage += self.pct_inc_value
            else: self.long_percentage = self.base_percentage
        working_amt = self.pct_calc_dollar_quantity() 
        self.buy(working_amt,price)

    def sell_pct(self,price):
        # Calculate how much your willing to use
        if self.increment_percentage == True : 
            if self.last_signal == "Short": self.short_percentage += self.pct_inc_value
            else: self.short_percentage = self.base_percentage
        working_amt = self.pct_calc_stock_quantity()
        self.sell(working_amt,price)

    def check_and_buy(self,price):
        if self.can_buy_pct(): self.buy_pct(price)
        
    def check_and_sell(self,price):
        if self.can_sell_pct(): self.sell_pct(price)
        
    def buy(self,working_amt:float,price):
        
        working_amt *= self.long_quantity_multi
        # Take dollars from the wallet
        self.full_dollar_quantity -= working_amt
        # Add The bought stocks to your wallet 
        self.full_stock_quantity += self.convert_dollar2stock(working_amt,closing_price=price)
        self.last_signal = "Long"
        print(f"[BUY]{price}")
        print(f"  +{self.convert_dollar2stock(working_amt,closing_price=price) } -(${working_amt})\n" )
        
    def sell(self,working_amt,price):
        working_amt *= self.short_quantity_multi
        # Take dollars from the wallet
        self.full_dollar_quantity += self.convert_stock2dollar(working_amt,closing_price=price) 
        
        self.last_signal = "Short"
        
        print(f"[SELL]{price}")
        print(f"  +${self.convert_stock2dollar(working_amt,closing_price=price) } -({working_amt})\n" )
        # Add The bought stocks to your wallet 
        self.full_stock_quantity -= working_amt
        
        
    def hold(self):
        raise NotImplemented
    
    
    def run_pct_based(self,):
        if not self.data_frame.empty:
            for idx, price  in enumerate(self.data_frame.close) :
                if self.analytics.Long.iloc[idx] == True: 
                    self.last_signal = "Long"
                    if self.can_buy_pct(): 
                        self.buy_pct(price)
                        self.successful_Long_trades += 1 
                    elif not self.can_buy_pct():
                        self.unsuccessful_trades += 1 
                elif self.analytics.Long.iloc[idx] == False: 
                    pass
                if self.analytics.Short.iloc[idx] == True: 
                    self.last_signal = "Short"
                    if self.can_sell_pct(): 
                        self.sell_pct(price)
                        self.successful_Short_trades += 1 
                    elif not self.can_sell_pct():
                        self.unsuccessful_trades += 1 
                elif self.analytics.Short.iloc[idx] == False:
                    pass


            final_price = self.data_frame.close.iloc[-1]
            self.ending_dollar_quantity = self.full_dollar_quantity
            self.ending_stock_quantity = self.full_stock_quantity
            self.amount_difference_dollars = self.ending_dollar_quantity - self.starting_dollar_quantity 
            self.amount_difference_stock =  self.ending_stock_quantity - self.starting_stock_quantity 
            self.converted_risked_stock = self.convert_stock2dollar(self.amount_risked_stock,final_price)
            self.converted_stock_quantity = self.convert_stock2dollar(self.full_stock_quantity,final_price)
            self.total_amount_risked = self.converted_risked_stock + self.amount_risked_dollars
            self.converted_difference_stock = self.convert_stock2dollar(self.amount_difference_stock,final_price)
            self.amount_difference_dollars =  round(self.amount_difference_dollars, 3 )
            self.amount_difference_stock =  round(self.amount_difference_stock, 3 )
            
            self.converted_risked_stock =  round(self.converted_risked_stock, 3 )
            self.converted_difference_stock =  round(self.converted_difference_stock, 3 )
            self.ending_total_value = self.convert_stock2dollar(self.full_stock_quantity,final_price) + self.full_dollar_quantity
            self.total_amount_difference = self.ending_total_value - self.starting_total_value
            self.full_stock_quantity = round(self.full_stock_quantity, 3 )
            self.full_dollar_quantity = round(self.full_dollar_quantity, 3 )
            self.ending_total_value = round(self.ending_total_value, 3)
            self.total_amount_risked = round(self.total_amount_risked ,3)
            self.total_amount_difference = round(self.total_amount_difference,3)
            self.converted_stock_quantity = round(self.converted_stock_quantity,3)
            print(f"\nEnding Values:" )
            
            print(f"Successful_trades: (Long: {self.successful_Long_trades}, Short: {self.successful_Short_trades})")
            print(f"Unsuccessful_trades: {self.unsuccessful_trades}")
            
            print(f"Amount Risked: (Dollars: {self.amount_risked_dollars}, Stock: {self.amount_risked_stock}({self.converted_risked_stock}) ")
            print(f"Amount Difference: (Dollars: {self.amount_difference_dollars}, Stock: {self.amount_difference_stock}({self.converted_difference_stock}) ")
            
            print(f"Total Amount Risked: {self.total_amount_risked}")
            print(f"Total Amount Difference: {self.total_amount_difference} ")
            print(f"  Wallet( Stock: {self.full_stock_quantity}({self.converted_stock_quantity}) / Fiat: {self.full_dollar_quantity} ) \n \
                  Worth:{self.ending_total_value} )")

        else: 
            print("Nothing to run: Empty DataFrame")
        



    def __call__(self, *args: Any, **kwds: Any) -> Any:
        print(
        f"Starting values \n" +
        f"    DataFrame:{not self.data_frame.empty}, Size: {len(self.data_frame)}.\n" +
        f"    Wallet( Stock: {self.full_stock_quantity} / Fiat: {self.full_dollar_quantity} ) ")     
        pass

