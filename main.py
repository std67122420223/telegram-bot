import os
import time
import yaml
import ccxt
import pandas as pd
import requests

# โหลดไฟล์ตั้งค่า Config
def load_config():
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ฟังก์ชันส่งข้อความเข้า Telegram ดึงรหัสจาก Environment บน Cloud
def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ [Error] ไม่พบข้อมูล TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID ใน Environment")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ ไม่สามารถส่งข้อความ Telegram ได้: {e}")

def main():
    print("🤖 [LIVE] บอทเริ่มเปิดระบบเฝ้ากราฟราคาทองคำจริงบน Cloud...")
    config = load_config()
    
    # เชื่อมต่อโบรกเกอร์ผ่าน CCXT (ใช้ Bybit เป็นหลักในการดึงราคาสปอต)
    exchange = ccxt.bybit()
    symbol = config['bot']['symbol']
    timeframe = config['bot']['timeframe']
    
    from strategy.smc_strategy import analyze_smc
    
    # --- ตัวแปรสำหรับระบบจำสถานะสัญญาณและการกันหน้าทุน ---
    active_position = None  # สถานะออเดอร์จำลอง: "BUY", "SELL" หรือ None
    entry_price = 0.0       # ราคาเข้าซื้อ
    current_sl = 0.0        # เส้น SL ปัจจุบัน
    current_tp = 0.0        # เส้น TP ปัจจุบัน
    is_be_protected = False # บันทึกว่าขยับบังหน้าทุนไปหรือยัง
    
    while True:
        try:
            # ดึงข้อมูลแท่งเทียนล่าสุด
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # วิเคราะห์กลยุทธ์
            buy_score, sell_score, current_price = analyze_smc(df)
            
            print(f"👀 [SCANNING] ราคาทองปัจจุบัน: {current_price:.2f} | คะแนน BUY: {buy_score}/8 | คะแนน SELL: {sell_score}/8")
            
            # =======================================================
            # 1. ระบบตรวจสอบและอัปเดตออเดอร์จำลอง (เช็กชน TP / SL / กันหน้าทุน)
            # =======================================================
            if active_position is not None:
                # --- กรณีถือสถานะ BUY ---
                if active_position == "BUY":
                    # เช็กชน SL
                    if current_price <= current_sl:
                        send_telegram_message(f"🛑 *[SMC SIGNAL: CLOSE]*\n📉 ออเดอร์ BUY ชนคัตขาดทุน (SL) แล้ว\n💵 ราคาปิด: {current_price:.2f}")
                        active_position = None
                    # เช็กชน TP
                    elif current_price >= current_tp:
                        send_telegram_message(f"🎯 *[SMC SIGNAL: TAKE PROFIT]*\n🎉 ออเดอร์ BUY ชนเป้ากำไร (TP) สำเร็จ!\n💵 ราคาปิด: {current_price:.2f}")
                        active_position = None
                    # เช็กเงื่อนไข "ขยับบังหน้าทุน BE" (พอกำไรวิ่งไปได้ครึ่งทางของเป้าหมาย และยังไม่เคยกันทุน)
                    elif not is_be_protected and current_price >= (entry_price + (config['strategy']['tp_pips'] / 200)):
                        current_sl = entry_price  # เลื่อนเส้น SL มาบังทุนเป๊ะๆ
                        is_be_protected = True
                        msg = f"🛡️ *[SMC SIGNAL: BREAK EVEN]*\n📈 บังหน้าทุนสำเร็จ (BUY)\n💵 ราคาทองคำปัจจุบัน: {current_price:.2f}\n🔐 ขยับ SL บังทุนที่: {entry_price:.2f}\n🎯 เป้าหมาย TP: {current_tp:.2f}"
                        send_telegram_message(msg)
                
                # --- กรณีถือสถานะ SELL ---
                elif active_position == "SELL":
                    # เช็กชน SL
                    if current_price >= current_sl:
                        send_telegram_message(f"🛑 *[SMC SIGNAL: CLOSE]*\n📈 ออเดอร์ SELL ชนคัตขาดทุน (SL) แล้ว\n💵 ราคาปิด: {current_price:.2f}")
                        active_position = None
                    # เช็กชน TP
                    elif current_price <= current_tp:
                        send_telegram_message(f"🎯 *[SMC SIGNAL: TAKE PROFIT]*\n🎉 ออเดอร์ SELL ชนเป้ากำไร (TP) สำเร็จ!\n💵 ราคาปิด: {current_price:.2f}")
                        active_position = None
                    # เช็กเงื่อนไข "ขยับบังหน้าทุน BE" (พอกำไรวิ่งลงมาได้ครึ่งทางของเป้าหมาย)
                    elif not is_be_protected and current_price <= (entry_price - (config['strategy']['tp_pips'] / 200)):
                        current_sl = entry_price  # เลื่อนเส้น SL มาบังทุนเป๊ะๆ
                        is_be_protected = True
                        msg = f"🛡️ *[SMC SIGNAL: BREAK EVEN]*\n📉 บังหน้าทุนสำเร็จ (SELL)\n💵 ราคาทองคำปัจจุบัน: {current_price:.2f}\n🔐 ขยับ SL บังทุนที่: {entry_price:.2f}\n🎯 เป้าหมาย TP: {current_tp:.2f}"
                        send_telegram_message(msg)

            # =======================================================
            # 2. ระบบออกสัญญาณใหม่ (หากไม่มีออเดอร์ค้างอยู่ และคะแนนเต็มหลอด)
            # =======================================================
            if active_position is None:
                # ตรวจสอบเงื่อนไขเปิดสัญญาณ BUY (คะแนนแตะเป้า)
                if buy_score >= config['strategy']['score_threshold']:
                    entry_price = current_price
                    # เปลี่ยนหาร 10 เป็นหาร 100 เพื่อให้ได้ระยะสั้นตรงความจริง (เช่น 800 pips = 8 ดอลลาร์)
                    current_sl = entry_price - (config['strategy']['sl_pips'] / 100)
                    current_tp = entry_price + (config['strategy']['tp_pips'] / 100)
                    active_position = "BUY"
                    is_be_protected = False
                    
                    msg = f"🔔 *[SMC SIGNAL: BUY]*\n📈 ราคาทองคำ: {entry_price:.2f}\n🎯 TP: {current_tp:.2f}\n🛑 SL: {current_sl:.2f}\n🔥 คะแนนความแม่นยำ: {buy_score}/8"
                    send_telegram_message(msg)
                    time.sleep(60) # หน่วงช่วงสั้นป้องกันส่งซิกซ้ำซ้อน
                    
                # ตรวจสอบเงื่อนไขเปิดสัญญาณ SELL
                elif sell_score >= config['strategy']['score_threshold']:
                    entry_price = current_price
                    # เปลี่ยนหาร 10 เป็นหาร 100 เพื่อความถูกต้องกระชับของราคาทองคำ
                    current_sl = entry_price + (config['strategy']['sl_pips'] / 100)
                    current_tp = entry_price - (config['strategy']['tp_pips'] / 100)
                    active_position = "SELL"
                    is_be_protected = False
                    
                    msg = f"🔔 *[SMC SIGNAL: SELL]*\n📉 ราคาทองคำ: {entry_price:.2f}\n🎯 TP: {current_tp:.2f}\n🛑 SL: {current_sl:.2f}\n🔥 คะแนนความแม่นยำ: {sell_score}/8"
                    send_telegram_message(msg)
                    time.sleep(60)

        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในระบบ: {e}")
            
        # หน่วงเวลาสแกนรอบถัดไปตามค่าวินาทีใน Config (60 วินาที)
        time.sleep(config['bot']['scan_interval_seconds'])

if __name__ == "__main__":
    main()