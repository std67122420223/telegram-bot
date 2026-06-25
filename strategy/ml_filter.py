import pandas as pd
import numpy as np
from xgboost import XGBClassifier

class MachineLearningSignalFilter:
    def __init__(self, config: dict):
        self.enabled = config['strategies']['ml_filter']['enabled']
        self.threshold = config['strategies']['ml_filter']['probability_threshold']
        self.model = XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.1, eval_metric='logloss')
        self._is_trained = False

    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = pd.DataFrame(index=df.index)
        features['returns'] = df['close'].pct_change()
        features['volatility'] = df['close'].pct_change().rolling(5).std()
        features.fillna(0, inplace=True)
        return features

    def filter_signal(self, df: pd.DataFrame) -> float:
        if not self.enabled or not self._is_trained:
            return 0.85 # ผ่านเกณฑ์พื้นฐานกรณีไม่มีข้อมูลฝึก
        try:
            X = self.generate_features(df).tail(1)
            prob = self.model.predict_proba(X)[0][1]
            return float(prob)
        except Exception:
            return 0.5