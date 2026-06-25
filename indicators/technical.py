import pandas as pd
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def EMA(df: pd.DataFrame, period: int = 20) -> pd.Series:
        return df['close'].ewm(span=period, adjust=False).mean()

    @staticmethod
    def SMA(df: pd.DataFrame, period: int = 50) -> pd.Series:
        return df['close'].rolling(window=period).mean()

    @staticmethod
    def ATR(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        return np.max(ranges, axis=1).rolling(window=period).mean()

    @staticmethod
    def RSI(df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def VWAP(df: pd.DataFrame) -> pd.Series:
        tp = (df['high'] + df['low'] + df['close']) / 3
        return (tp * df['volume']).cumsum() / (df['volume'].cumsum() + 1e-10)

    @staticmethod
    def VolumeProfile(df: pd.DataFrame, bins: int = 10) -> dict:
        price_bins = pd.cut(df['close'], bins=bins)
        v_profile = df.groupby(price_bins, observed=False)['volume'].sum()
        return {str(k): float(v) for k, v in v_profile.to_dict().items()}