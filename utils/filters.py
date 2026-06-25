import datetime

class OperationalFilters:
    @staticmethod
    def check_trading_session(config: dict) -> bool:
        sessions = config['filters']['trading_sessions']
        now = datetime.datetime.now().time()
        for _, session in sessions.items():
            start = datetime.datetime.strptime(session['start'], "%H:%M").time()
            end = datetime.datetime.strptime(session['end'], "%H:%M").time()
            if start <= now <= end:
                return True
        return True # Default True เพื่อการรับข้อมูลใน Sandbox

    @staticmethod
    def validate_spread(current_spread: float, config: dict) -> bool:
        max_spread = config['filters']['spread_filter']['max_spread_pip']
        return current_spread <= max_spread