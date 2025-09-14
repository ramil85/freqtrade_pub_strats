# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import DecimalParameter, IntParameter
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

# docker compose run --rm freqtrade hyperopt `
# --strategy ADX_15M_USDT `
# --hyperopt-loss SharpeHyperOptLoss `
# --config user_data/config.json `
# --timerange 20230101-20250907 `
# --spaces default `
# --epochs 100

class ADX_15M_USDT(IStrategy):
    # Timeframe - updated from ticker_interval
    timeframe = '15m'

    # ROI table:
    minimal_roi = {
        "0": 0.26552,
        "30": 0.10255,
        "210": 0.03545,
        "540": 0
    }

    # Stoploss:
    stoploss = -0.1255
    
    # Can this strategy go short?
    can_short: bool = False
    
    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30
    
    # Hyperoptimizable parameters
    adx_buy_threshold = IntParameter(10, 25, default=16, space="buy")
    minus_di_buy_threshold = IntParameter(2, 10, default=4, space="buy") 
    plus_di_buy_threshold = IntParameter(15, 30, default=20, space="buy")
    
    adx_sell_threshold = IntParameter(35, 55, default=43, space="sell")
    minus_di_sell_threshold = IntParameter(15, 35, default=22, space="sell")
    plus_di_sell_threshold = IntParameter(15, 30, default=20, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Get parameter values - use defaults if hyperopt parameters don't exist
        adx_buy = getattr(self, 'adx_buy_threshold', None)
        adx_buy_val = adx_buy.value if adx_buy else 16
        
        minus_di_buy = getattr(self, 'minus_di_buy_threshold', None) 
        minus_di_buy_val = minus_di_buy.value if minus_di_buy else 4
        
        plus_di_buy = getattr(self, 'plus_di_buy_threshold', None)
        plus_di_buy_val = plus_di_buy.value if plus_di_buy else 20
        
        adx_sell = getattr(self, 'adx_sell_threshold', None)
        adx_sell_val = adx_sell.value if adx_sell else 43
        
        minus_di_sell = getattr(self, 'minus_di_sell_threshold', None)
        minus_di_sell_val = minus_di_sell.value if minus_di_sell else 22
        
        plus_di_sell = getattr(self, 'plus_di_sell_threshold', None)
        plus_di_sell_val = plus_di_sell.value if plus_di_sell else 20
        
        # Calculate indicators
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=25)
        dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod=25)
        dataframe['sar'] = ta.SAR(dataframe)
        dataframe['mom'] = ta.MOM(dataframe, timeperiod=14)

        # For sell signals - using same indicators, no need to duplicate
        dataframe['sell-adx'] = dataframe['adx']
        dataframe['sell-plus_di'] = dataframe['plus_di'] 
        dataframe['sell-minus_di'] = dataframe['minus_di']
        dataframe['sell-sar'] = dataframe['sar']
        dataframe['sell-mom'] = dataframe['mom']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Get parameter values - use defaults if hyperopt parameters don't exist
        adx_buy = getattr(self, 'adx_buy_threshold', None)
        adx_buy_val = adx_buy.value if adx_buy else 16
        
        minus_di_buy = getattr(self, 'minus_di_buy_threshold', None) 
        minus_di_buy_val = minus_di_buy.value if minus_di_buy else 4
        
        plus_di_buy = getattr(self, 'plus_di_buy_threshold', None)
        plus_di_buy_val = plus_di_buy.value if plus_di_buy else 20
        
        dataframe.loc[
            (
                (dataframe['adx'] > adx_buy_val) &
                (dataframe['minus_di'] > minus_di_buy_val) &
                (dataframe['plus_di'] > plus_di_buy_val) &
                (qtpylib.crossed_above(dataframe['plus_di'], dataframe['minus_di']))
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Get parameter values - use defaults if hyperopt parameters don't exist
        adx_sell = getattr(self, 'adx_sell_threshold', None)
        adx_sell_val = adx_sell.value if adx_sell else 43
        
        minus_di_sell = getattr(self, 'minus_di_sell_threshold', None)
        minus_di_sell_val = minus_di_sell.value if minus_di_sell else 22
        
        plus_di_sell = getattr(self, 'plus_di_sell_threshold', None)
        plus_di_sell_val = plus_di_sell.value if plus_di_sell else 20
        
        dataframe.loc[
            (
                (dataframe['adx'] > adx_sell_val) &
                (dataframe['minus_di'] > minus_di_sell_val) &
                (dataframe['plus_di'] > plus_di_sell_val) &
                (qtpylib.crossed_above(dataframe['sell-minus_di'], dataframe['sell-plus_di']))
            ),
            'exit_long'] = 1
        return dataframe
