import os
from sqlalchemy import create_engine
import datetime
from sqlalchemy.orm import sessionmaker
from database.models import Base, TradeRecord

class DatabaseManager:
    def __init__(self):
        db_url = os.getenv("DB_URL", "sqlite:///trading_system.db")
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_trade(self, trade_data: dict) -> bool:
        session = self.Session()
        try:
            trade = TradeRecord(**trade_data)
            session.add(trade)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def close_trade(self, ticket_id: str, exit_price: float, pnl: float) -> bool:
        session = self.Session()
        try:
            trade = session.query(TradeRecord).filter(TradeRecord.ticket_id == ticket_id).first()
            if trade:
                trade.exit_price = exit_price
                trade.pnl = pnl
                trade.status = "CLOSED"
                trade.closed_at = datetime.datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()