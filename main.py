import os
import time
import yaml
import requests
import ccxt
import pandas as pd
from strategy.smc_strategy import SmartMoneyConceptsStrategy

class LiveGoldTradingBot:
    def __init__(self):
        # โหลดค่าคอนฟิก
        with open(os.path.join("config", "config.yaml"), "r") as f:
            self.config = yaml.safe_load(f)
        
        # ดึงรหัส Telegram จากระบบ
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "7123456789:AAF_ExampleTokenXYZ_YOUR_ACTUAL_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "987654321")
        
        self.strategy = SmartMoneyConceptsStrategy(self.config)
        
        # เชื่อมต่อดึงราคาทองคำจริงผ่านตลาดสปอต/ฟิวเจอร์ส
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        
        self.active_order = None 

    def send_telegram(self, message: str):
        """ส่งข้อความตรงเข้า Telegram API"""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"❌ Telegram Connection Error: {e}")

    def fetch_live_gold_price(self) -> tuple[pd.DataFrame, float]:
        """ดึงราคาทองคำจริงจากตลาดโลก"""
        try:
            ticker = self.exchange.fetch_ticker('PAXG/USDT')
            current_price = float(ticker['last'])
            
            # ดึงแท่งเทียน 5m ตามมาตรฐาน API 
            ohlcv = self.exchange.fetch_ohlcv('PAXG/USDT', timeframe='5m', limit=5)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df, current_price
        except Exception as e:
            print(f"❌ ไม่สามารถดึงราคาทองคำสดจากเซิร์ฟเวอร์ได้: {e}")
            return pd.DataFrame(), 0.0

    def run_live_pipeline(self):
        print("🤖 [LIVE] บอทเริ่มเปิดระบบเฝ้ากราฟราคาทองคำจริง (XAUUSD/PAXG) ตลอด 24 ชม. แล้ว...")
        
        while True:
            try:
                df, current_price = self.fetch_live_gold_price()
                if df.empty or current_price == 0.0:
                    print("⚠️ [WARNING] ไม่สามารถดึงราคาได้ กำลังลองใหม่ในอีก 5 วินาที...")
                    time.sleep(5)
                    continue

                # 1. จังหวะไม่มีออเดอร์: สแกนหากราฟเข้าโซนปลอดภัย (สูตร SMC)
                if self.active_order is None:
                    analysis = self.strategy.analyze_market_structure(df)
                    
                    # 💡 บรรทัดรายงานราคาและคะแนนสดบนหน้าจอ Terminal
                    print(f"👀 [SCANNING] ทองคำปัจจุบัน: {current_price} | คะแนน BUY: {analysis['buy_score']}/8 | คะแนน SELL: {analysis['sell_score']}/8")
                    
                    if analysis["signal"] in ["BUY", "SELL"]:
                        # คำนวณกรอบระยะจุดทองคำ: SL 700 จุด ($7) / TP 1500 จุด ($15)
                        self.active_order = {
                            "direction": analysis["signal"],
                            "entry_price": current_price,
                            "sl": current_price + 7.0 if analysis["signal"] == "SELL" else current_price - 7.0,
                            "tp": current_price - 15.0 if analysis["signal"] == "SELL" else current_price + 15.0,
                            "is_breakeven_notified": False
                        }
                        
                        # แจ้งเตือนซิกแนลจุดเข้าจริงเข้า Telegram
                        msg = (
                            f"🚨 XAUUSD SIGNAL (LIVE)\n\n"
                            f"ตามๆ : {self.active_order['direction']}\n\n"
                            f"จุดเข้าปลอดภัย : {round(self.active_order['entry_price'], 2)}\n"
                            f"SL : {round(self.active_order['sl'], 2)} (-700 จุด)\n"
                            f"TP : {round(self.active_order['tp'], 2)} (+1500 จุด)\n\n"
                            f"คะแนนความปลอดภัย : 8 เต็ม 8\n"
                            f"🔔 สถานะ: เข้าสู่โซนอัตราชนะสูง (RR 1:2)"
                        )
                        self.send_telegram(msg)
                        print(f"🔥 [SIGNAL TRIGGERED] ยิงสัญญาณเข้า Telegram แล้ว! ฝั่ง {analysis['signal']} ที่ราคา {current_price}")

                # 2. จังหวะมีออเดอร์ค้างอยู่: ตรวจสอบราคาระหว่างวันแบบ Dynamic
                else:
                    order = self.active_order
                    direction = order["direction"]
                    entry = order["entry_price"]
                    
                    pips_moved = (entry - current_price) * 100 if direction == "SELL" else (current_price - entry) * 100
                    
                    print(f"📊 [LIVE TRACK] ถือ {direction} | เข้า: {round(entry,2)} | ปัจจุบัน: {round(current_price,2)} | ระยะวิ่ง: {round(pips_moved,0)} จุด")

                    # กฎข้อที่ 1: วิ่งถูกทางไปถึง 500 จุด -> แจ้งกันทุน
                    if pips_moved >= 500.0 and not order["is_breakeven_notified"]:
                        self.send_telegram("🔒 กันหน้าทุน (ราคาทองคำวิ่งถูกทางไปแล้ว 500 จุด)")
                        self.active_order["is_breakeven_notified"] = True
                        print("🔒 [STATUS] ยิงซิกเนลกันหน้าทุนสำเร็จ")

                    # กฎข้อที่ 2: ราคาวิ่งไปชนเป้าทำกำไร -> แจ้งเตือนกำไร (TP 1500 จุด)
                    elif (direction == "SELL" and current_price <= order["tp"]) or (direction == "BUY" and current_price >= order["tp"]):
                        self.send_telegram("💰 กำไร (ราคาทองคำพุ่งชนเป้าหมายทำกำไร TP 1500 จุด เรียบร้อยแล้ว)")
                        print("💰 [CLOSED] ออเดอร์จบด้วยผลกำไร (TP)")
                        self.active_order = None
                        time.sleep(10)

                    # กฎข้อที่ 3: ราคาวิ่งสะบัดผิดทางไปชนเส้นตัดขาดทุน -> แจ้งเตือนขาดทุน (SL 700 จุด)
                    elif (direction == "SELL" and current_price >= order["sl"]) or (direction == "BUY" and current_price <= order["sl"]):
                        self.send_telegram("🛑 ขาดทุน (ราคาทองคำสะบัดชนเส้นคัทขาดทุน SL 700 จุด)")
                        print("🛑 [CLOSED] ออเดอร์จบด้วยผลขาดทุน (SL)")
                        self.active_order = None
                        time.sleep(10)

                time.sleep(60)

            except Exception as e:
                print(f"เกิดข้อผิดพลาดในระบบลูป: {e}")
                time.sleep(60)

if __name__ == '__main__':
    bot = LiveGoldTradingBot()
    bot.run_live_pipeline()