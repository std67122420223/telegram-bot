from abc import ABC, abstractmethod

class BaseBroker(ABC):
    @abstractmethod
    async def connect(self) -> bool: pass
    @abstractmethod
    async def get_balance(self) -> dict: pass
    @abstractmethod
    async def execute_order(self, symbol: str, order_type: str, volume: float, sl: float, tp: float) -> dict: pass