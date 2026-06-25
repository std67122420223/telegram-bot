class RiskManager:
    def __init__(self, config: dict):
        self.rm_config = config['risk_management']

    def calculate_lot_size(self, balance: float, equity: float, stop_loss_pips: float, pip_value: float) -> float:
        try:
            mode = self.rm_config['mode']
            if mode == "fixed_lot":
                return 0.1
            elif mode == "risk_pct":
                risk_amt = balance * (self.rm_config['risk_percentage'] / 100.0)
                lot_size = risk_amt / (stop_loss_pips * pip_value + 1e-10)
                return max(0.01, round(lot_size, 2))
            return 0.01
        except Exception:
            return 0.01

    def validate_daily_limits(self, daily_loss_pct: float, drawdown_pct: float) -> bool:
        if daily_loss_pct >= self.rm_config['max_daily_loss_pct']:
            return False
        if drawdown_pct >= self.rm_config['max_drawdown_pct']:
            return False
        return True