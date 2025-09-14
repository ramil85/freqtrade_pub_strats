# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta
# --------------------------------

# docker compose run --rm freqtrade hyperopt `
# --strategy ADXMomentum `
# --hyperopt-loss SharpeHyperOptLoss `
# --config user_data/config_2.json `
# --timerange 20230101-20250907 `
# --spaces roi stoploss `
# --epochs 100


class ADXMomentum(IStrategy):
    """
    author@: Gert Wohlgemuth
    converted from:
        https://github.com/sthewissen/Mynt/blob/master/src/Mynt.Core/Strategies/AdxMomentum.cs
    
    Updated for Freqtrade 2025.8
    """
    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.01
    }
    
    # Optimal stoploss designed for the strategy
    stoploss = -0.25
    
    # Optimal timeframe for the strategy
    timeframe = '1h'
    
    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30  # Increased from 20 to be safe with indicators
    
    # Can this strategy go short?
    can_short: bool = False
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate indicators for the strategy
        """
        try:
            # ADX (Average Directional Index)
            dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
            
            # Directional Movement Indicators
            dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=25)
            dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod=25)
            
            # Parabolic SAR
            dataframe['sar'] = ta.SAR(dataframe)
            
            # Momentum
            dataframe['mom'] = ta.MOM(dataframe, timeperiod=14)
            
        except Exception as e:
            print(f"Error in populate_indicators: {e}")
            # Fallback calculations if TA-Lib fails
            dataframe['adx'] = 0
            dataframe['plus_di'] = 0
            dataframe['minus_di'] = 0
            dataframe['sar'] = dataframe['close']
            dataframe['mom'] = dataframe['close'].pct_change(14) * 100
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        # Get parameter values - use defaults if hyperopt parameters don't exist
        adx_threshold = getattr(self, 'adx_threshold', None)
        adx_threshold_val = adx_threshold.value if adx_threshold else 25
        
        dataframe.loc[
            (
                (dataframe['adx'] > adx_threshold_val) &
                (dataframe['mom'] > 0) &
                (dataframe['minus_di'] > adx_threshold_val) &
                (dataframe['plus_di'] > dataframe['minus_di'])
            ),
            'enter_long'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """
        # Get parameter values - use defaults if hyperopt parameters don't exist
        exit_adx_threshold = getattr(self, 'exit_adx_threshold', None)
        exit_adx_threshold_val = exit_adx_threshold.value if exit_adx_threshold else 25
        
        exit_minus_di_threshold = getattr(self, 'exit_minus_di_threshold', None)
        exit_minus_di_threshold_val = exit_minus_di_threshold.value if exit_minus_di_threshold else 25
        
        dataframe.loc[
            (
                (dataframe['adx'] > exit_adx_threshold_val) &
                (dataframe['mom'] < 0) &
                (dataframe['minus_di'] > exit_minus_di_threshold_val) &
                (dataframe['plus_di'] < dataframe['minus_di'])
            ),
            'exit_long'] = 1
        
        return dataframe
